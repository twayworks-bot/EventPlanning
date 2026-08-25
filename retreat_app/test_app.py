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
            'remark': '비고란',
            'category_large': '테스트대분류',
            'category_medium': '테스트중분류',
            'category_small': '테스트소분류',
            'due_date': '-5d'
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
        cursor.execute("SELECT * FROM checklists WHERE event_id = 1 AND item_no = 56")
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row['content'], '새로운 테스트 업무')
        self.assertEqual(row['category_large'], '테스트대분류')
        self.assertEqual(row['category_medium'], '테스트중분류')
        self.assertEqual(row['category_small'], '테스트소분류')
        self.assertEqual(row['due_date'], '-5d')
        conn.close()

    def test_update_checklist_item(self):
        # Get an item to edit
        conn = flask_app.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM checklists WHERE event_id = 1 LIMIT 1")
        item_id = cursor.fetchone()['id']
        conn.close()

        update_data = {
            'content': '수정된 테스트 업무',
            'assignee': '수정테스터',
            'check_point': '수정통과 확인',
            'remark': '수정비고란',
            'category_large': '수정대분류',
            'category_medium': '수정중분류',
            'category_small': '수정소분류',
            'due_date': '-3d'
        }
        response = self.app.put(f'/api/checklists/{item_id}',
                                data=json.dumps(update_data),
                                content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # Verify updated in database
        conn = flask_app.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM checklists WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row['content'], '수정된 테스트 업무')
        self.assertEqual(row['assignee'], '수정테스터')
        self.assertEqual(row['category_large'], '수정대분류')
        self.assertEqual(row['category_medium'], '수정중분류')
        self.assertEqual(row['category_small'], '수정소분류')
        self.assertEqual(row['due_date'], '-3d')
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

    def test_get_templates_empty(self):
        response = self.app.get('/api/templates')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 0)

    def test_save_template_and_get(self):
        # Save custom template
        template_payload = {
            'name': '겨울 수련회 표준 템플릿',
            'items': [
                {
                    'category_large': '행사기획',
                    'category_medium': '홍보',
                    'category_small': '현수막',
                    'content': '현수막 시안 디자인',
                    'assignee': '디자이너',
                    'check_point': '오탈자 확인',
                    'remark': '3층 대강당용',
                    'due_date': '-15d'
                },
                {
                    'category_large': '시설운영',
                    'category_medium': '숙소',
                    'category_small': '방배정',
                    'content': '숙소 방 배정안 작성',
                    'assignee': '간사',
                    'check_point': '연령대 고려',
                    'remark': '',
                    'due_date': '-3d'
                }
            ]
        }
        
        response = self.app.post('/api/templates',
                                 data=json.dumps(template_payload),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('id', data)
        template_id = data['id']

        # Get all templates
        response = self.app.get('/api/templates')
        self.assertEqual(response.status_code, 200)
        templates_list = json.loads(response.data)
        self.assertEqual(len(templates_list), 1)
        self.assertEqual(templates_list[0]['name'], '겨울 수련회 표준 템플릿')

        # Get single template details
        response = self.app.get(f'/api/templates/{template_id}')
        self.assertEqual(response.status_code, 200)
        details = json.loads(response.data)
        self.assertEqual(details['name'], '겨울 수련회 표준 템플릿')
        self.assertEqual(len(details['items']), 2)
        self.assertEqual(details['items'][0]['content'], '현수막 시안 디자인')
        self.assertEqual(details['items'][0]['due_date'], '-15d')

    def test_create_event_with_custom_template(self):
        # 1. Create a custom template
        template_payload = {
            'name': '특수 소형 행사 템플릿',
            'items': [
                {
                    'category_large': '기획',
                    'category_medium': '예산',
                    'category_small': '확정',
                    'content': '예산안 최종 결재',
                    'assignee': '회계',
                    'check_point': '계산 검증',
                    'remark': '',
                    'due_date': '-7d'
                }
            ]
        }
        response = self.app.post('/api/templates',
                                 data=json.dumps(template_payload),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 201)
        template_id = json.loads(response.data)['id']

        # 2. Create new event using this template_id
        new_event = {
            'title': '2026 청년부 MT',
            'event_date': '2026-09-12',
            'description': '강촌 가평 엠티',
            'template_id': template_id
        }
        response = self.app.post('/api/events',
                                 data=json.dumps(new_event),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 201)
        event_id = json.loads(response.data)['id']

        # 3. Verify checklist items were correctly copied
        response = self.app.get(f'/api/events/{event_id}/checklists')
        self.assertEqual(response.status_code, 200)
        checklists = json.loads(response.data)
        self.assertEqual(len(checklists), 1)
        self.assertEqual(checklists[0]['content'], '예산안 최종 결재')
        self.assertEqual(checklists[0]['category_large'], '기획')
        self.assertEqual(checklists[0]['due_date'], '-7d')

    def test_delete_template(self):
        # 1. Create template
        template_payload = {
            'name': '삭제 대상 템플릿',
            'items': [{'content': '임시 과업'}]
        }
        response = self.app.post('/api/templates',
                                 data=json.dumps(template_payload),
                                 content_type='application/json')
        template_id = json.loads(response.data)['id']

        # Verify template exists
        response = self.app.get(f'/api/templates/{template_id}')
        self.assertEqual(response.status_code, 200)

        # 2. Delete template
        response = self.app.delete(f'/api/templates/{template_id}')
        self.assertEqual(response.status_code, 200)

        # 3. Verify deleted (GET details returns 404)
        response = self.app.get(f'/api/templates/{template_id}')
        self.assertEqual(response.status_code, 404)

        # Verify cascade deletion of template_items in database
        conn = flask_app.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM template_items WHERE template_id = ?", (template_id,))
        self.assertEqual(cursor.fetchone()[0], 0)
        conn.close()

if __name__ == '__main__':
    unittest.main()
