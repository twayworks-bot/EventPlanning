import os
import unittest
import json
import sqlite3
import app as flask_app

class RetreatAppTestCase(unittest.TestCase):
    def setUp(self):
        # Set database to a separate test database
        flask_app.DB_NAME = 'test_checklist.db'
        
        # Clear any existing test database
        if os.path.exists(flask_app.DB_NAME):
            os.remove(flask_app.DB_NAME)
            
        flask_app.app.config['TESTING'] = True
        self.app = flask_app.app.test_client()
        
        # Initialize test database
        flask_app.init_db()

    def tearDown(self):
        # Remove test database after tests
        if os.path.exists(flask_app.DB_NAME):
            try:
                os.remove(flask_app.DB_NAME)
            except PermissionError:
                pass

    def test_db_seeding(self):
        # Check if the database was initialized with the default event
        conn = flask_app.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events")
        event_count = cursor.fetchone()[0]
        self.assertEqual(event_count, 1)

        # Check if default event checklists were seeded
        cursor.execute("SELECT COUNT(*) FROM checklists WHERE event_id = 1")
        checklist_count = cursor.fetchone()[0]
        self.assertEqual(checklist_count, 55)
        conn.close()

    def test_get_events(self):
        response = self.app.get('/api/events')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], "2026 하계수련회")

    def test_create_event_without_copy(self):
        new_event = {
            'title': '2026 겨울 수련회',
            'event_date': '2026-12-25',
            'description': '겨울 수련회 설명',
            'copy_template': False
        }
        response = self.app.post('/api/events', 
                                 data=json.dumps(new_event), 
                                 content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('id', data)
        
        # Verify event was inserted
        conn = flask_app.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events")
        self.assertEqual(cursor.fetchone()[0], 2)
        
        # Verify no checklist items copied
        cursor.execute("SELECT COUNT(*) FROM checklists WHERE event_id = ?", (data['id'],))
        self.assertEqual(cursor.fetchone()[0], 0)
        conn.close()

    def test_create_event_with_copy(self):
        new_event = {
            'title': '2026 가을 수련회',
            'event_date': '2026-10-10',
            'description': '가을 수련회 설명',
            'copy_template': True
        }
        response = self.app.post('/api/events', 
                                 data=json.dumps(new_event), 
                                 content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        new_event_id = data['id']
        
        # Verify 55 checklist items were copied
        conn = flask_app.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM checklists WHERE event_id = ?", (new_event_id,))
        self.assertEqual(cursor.fetchone()[0], 55)
        conn.close()

    def test_get_checklists(self):
        response = self.app.get('/api/events/1/checklists')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 55)
        self.assertEqual(data[0]['item_no'], 1)
        self.assertEqual(data[0]['content'], "전체일정관리")

    def test_add_checklist_item(self):
        item_data = {
            'content': '새로운 테스트 업무',
            'assignee': '테스터',
            'check_point': '통과 확인',
            'remark': '비고란'
        }
        response = self.app.post('/api/events/1/checklists',
                                 data=json.dumps(item_data),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['item_no'], 56)
        
        # Verify insertion in database
        conn = flask_app.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM checklists WHERE event_id = 1")
        self.assertEqual(cursor.fetchone()[0], 56)
        conn.close()

    def test_toggle_checklist(self):
        # Toggle item_id 1 (which belongs to seeded checklist)
        # Seeded item has checklists id starting from 1 (or cursor.lastrowid)
        # Let's query db first to get a valid checklist ID
        conn = flask_app.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, is_completed FROM checklists LIMIT 1")
        item = cursor.fetchone()
        item_id = item['id']
        self.assertEqual(item['is_completed'], 0)
        conn.close()

        # Toggle to completed
        toggle_data = {'is_completed': True}
        response = self.app.post(f'/api/checklists/{item_id}/toggle',
                                 data=json.dumps(toggle_data),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['is_completed'], 1)

        # Verify updated in database
        conn = flask_app.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT is_completed FROM checklists WHERE id = ?", (item_id,))
        self.assertEqual(cursor.fetchone()[0], 1)
        conn.close()

    def test_delete_checklist_item(self):
        conn = flask_app.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM checklists LIMIT 1")
        item_id = cursor.fetchone()['id']
        conn.close()

        response = self.app.delete(f'/api/checklists/{item_id}')
        self.assertEqual(response.status_code, 200)

        # Verify deleted in database
        conn = flask_app.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM checklists WHERE id = ?", (item_id,))
        self.assertEqual(cursor.fetchone()[0], 0)
        conn.close()

if __name__ == '__main__':
    unittest.main()
