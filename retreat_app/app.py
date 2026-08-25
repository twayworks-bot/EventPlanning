import sqlite3
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
DB_NAME = 'checklist.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# 1. DB 테이블 초기화 및 템플릿 데이터 시딩
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 행사 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            event_date TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 템플릿 마스터 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS event_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 템플릿 아이템 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS template_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER NOT NULL,
            item_no INTEGER NOT NULL,
            category_large TEXT DEFAULT '',
            category_medium TEXT DEFAULT '',
            category_small TEXT DEFAULT '',
            content TEXT NOT NULL,
            assignee TEXT DEFAULT '',
            check_point TEXT DEFAULT '',
            remark TEXT DEFAULT '',
            due_date TEXT DEFAULT '',
            FOREIGN KEY (template_id) REFERENCES event_templates (id) ON DELETE CASCADE
        )
    ''')
    
    # 체크리스트 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checklists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            item_no INTEGER NOT NULL,
            content TEXT NOT NULL,
            assignee TEXT,
            check_point TEXT,
            remark TEXT,
            is_completed INTEGER DEFAULT 0,
            category_large TEXT DEFAULT '',
            category_medium TEXT DEFAULT '',
            category_small TEXT DEFAULT '',
            due_date TEXT DEFAULT '',
            FOREIGN KEY (event_id) REFERENCES events (id) ON DELETE CASCADE
        )
    ''')
    
    # 기존 DB 컬럼 추가 마이그레이션
    cursor.execute("PRAGMA table_info(checklists)")
    columns = [row['name'] for row in cursor.fetchall()]
    if 'category_large' not in columns:
        cursor.execute("ALTER TABLE checklists ADD COLUMN category_large TEXT DEFAULT ''")
    if 'category_medium' not in columns:
        cursor.execute("ALTER TABLE checklists ADD COLUMN category_medium TEXT DEFAULT ''")
    if 'category_small' not in columns:
        cursor.execute("ALTER TABLE checklists ADD COLUMN category_small TEXT DEFAULT ''")
    if 'due_date' not in columns:
        cursor.execute("ALTER TABLE checklists ADD COLUMN due_date TEXT DEFAULT ''")
    
    # 기본 행사가 없을 경우 2026 하계수련회 생성 및 초기 55개 데이터 등록
    cursor.execute("SELECT COUNT(*) FROM events")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO events (title, event_date, description) VALUES (?, ?, ?)",
            ("2026 하계수련회", "2026-08-15", "모나파크 용평리조트 전교인 하계수련회")
        )
        default_event_id = cursor.lastrowid
        
        fallback_data = [
            (1, "전체일정관리", "음수민, 고대섭", "", ""),
            (2, "수련회 참석자 접수", "정현옥", "명단정리", ""),
            (3, "여행자보험", "정현옥", "", ""),
            (4, "회비수령 및 비용지출", "정현옥", "", ""),
            (5, "모나파크 관련 대응", "고대섭", "물놀이/숙소/부속홀", "의무실 세팅, 대강당 입구 책상 6개, 냉수기 2대, 온수기 1대, 식당 및 냉장고 협조, 교사휴게실, 누리홀(영성세미나)"),
            (6, "버스예약", "윤보선", "예약/기사연락처", "버스 정차 위치, 도면 및 안내 공지"),
            (7, "버스배정(학생/청년)", "음수민/육지승", "", ""),
            (8, "버스배정(장년)", "강민숙", "", ""),
            (9, "버스차장 카톡방 개설", "각 버스차장", "", ""),
            (10, "숙소배정(학생)", "음수민", "", ""),
            (11, "숙소배정(청년)", "육지승", "", ""),
            (12, "숙소배정(장년)", "이윤정, 유정숙", "", ""),
            (13, "호실별 카톡방 개설", "각 호실 방장", "", ""),
            (14, "주일예배 주보출력", "부목사님", "", ""),
            (15, "행사공동물품 상차", "우복태", "", ""),
            (16, "버스 간식준비", "여전도회", "", ""),
            (17, "버스출발", "버스차장, 부차장", "", ""),
            (18, "늦은 출발자 물품 확인", "차량배정팀에서 자차 확인", "", ""),
            (19, "수련회 환영준비", "선발대", "", ""),
            (20, "방송 음향시설 셋팅", "방송부", "", ""),
            (21, "운영팀 데스크 설치", "선발대", "", ""),
            (22, "의무실/교사휴게실 셋팅", "선발대", "", ""),
            (23, "환영 및 개회식", "음수민/고대섭", "", ""),
            (24, "학생팀파워", "HSS교사", "", ""),
            (25, "세례식", "이창현, 권사회", "", ""),
            (26, "담임목사님 세미나", "총단(이서영)", "", ""),
            (27, "학년별 모임", "총단(이서영)", "", ""),
            (28, "첫날 저녁 불침번", "남전도회(담당자: 마라나타), 여전도회: ?", "", ""),
            (29, "주일낮예배", "새가족부(우복태)", "", ""),
            (30, "단체사진촬영", "정원용, 정충성, 배금진, 이광섭(드론)", "", ""),
            (31, "물놀이", "음수민", "", ""),
            (32, "레크레이션/장기자랑", "김영진", "", ""),
            (33, "토요일 저녁예배", "새가족부(우복태)", "", ""),
            (34, "주일저녁예배", "새가족부(우복태)", "", ""),
            (35, "둘째날 저녁 불침번", "남전도회(담당자), 여전도회 담당자", "", ""),
            (36, "폐회식", "고대섭", "", ""),
            (37, "행사공동물품 귀경 상차", "남전도회", "", ""),
            (38, "간식준비", "여전도회", "", ""),
            (39, "현수막제작(대강당)", "김다영", "", ""),
            (40, "공지용 일정표(전지3장)", "김다영", "", ""),
            (41, "차량, 숙소명단 출력", "김다영", "", ""),
            (42, "청/장년부 명찰 제작", "청년부(육지승)", "", ""),
            (43, "예배전 대강당 청소정리", "봉사부장", "", ""),
            (44, "예배 성찬 준비", "권사회장", "", ""),
            (45, "음향장비", "방송부", "", ""),
            (46, "악기", "정원용, 이찬근", "", ""),
            (47, "사진기록", "정충성", "", ""),
            (48, "동영상기록", "배금진", "", ""),
            (49, "현장중계", "HSS교사", "", ""),
            (50, "학생들 규합(신입 위주)", "HSS교사", "", ""),
            (51, "의료지원팀 운영", "김현영", "", ""),
            (52, "학생리더 단톡방 만들기", "각팀별 진행", "", ""),
            (53, "주일저녁 서울가는 버스 배정", "담당자 : 강민숙", "", ""),
            (54, "도착 후 귀가안내", "서미혜", "", ""),
            (55, "수련회 귀가 후 짐정리", "청장년부/행사지원팀", "", "")
        ]
        
        for item in fallback_data:
            item_no = item[0]
            cat_l, cat_m, cat_s, due = "", "", "", ""
            
            # 일부 샘플 데이터에 체계적인 카테고리와 due-date 지정
            if item_no == 1:
                cat_l, cat_m, cat_s, due = "행사운영", "기획", "총괄", "-30d"
            elif item_no == 2:
                cat_l, cat_m, cat_s, due = "행사운영", "접수", "등록", "-15d"
            elif item_no in (3, 4):
                cat_l, cat_m, cat_s, due = "행사운영", "접수", "행정", "-10d"
            elif item_no in (6, 7, 8, 9):
                cat_l, cat_m, cat_s, due = "수송", "차량배정", "버스", "-10d"
            elif item_no in (10, 11, 12, 13):
                cat_l, cat_m, cat_s, due = "행사운영", "숙소배정", "호실", "-5d"
            elif item_no == 20:
                cat_l, cat_m, cat_s, due = "방송", "계약", "음향/조명계약", "-3d"
            elif item_no in (14, 25, 26, 27, 29, 33, 34, 44):
                cat_l, cat_m, cat_s, due = "예배", "준비", "집회", "-1d"
            elif item_no in (45, 46, 47, 48, 49):
                cat_l, cat_m, cat_s, due = "방송", "장비", "미디어", "-2d"
            elif item_no in (5, 15, 21, 22):
                cat_l, cat_m, cat_s, due = "현장운영", "셋팅", "시설", "-1d"
            elif item_no in (16, 28, 35, 38):
                cat_l, cat_m, cat_s, due = "행사운영", "지원", "봉사", "0d"
            elif item_no in (23, 24, 30, 31, 32, 36, 50, 51):
                cat_l, cat_m, cat_s, due = "현장운영", "진행", "프로그램", "0d"
            elif item_no in (17, 18, 19, 37, 52, 53, 54, 55):
                cat_l, cat_m, cat_s, due = "수송", "귀가", "복귀", "+1d"

            cursor.execute('''
                INSERT INTO checklists (event_id, item_no, content, assignee, check_point, remark, category_large, category_medium, category_small, due_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (default_event_id, item[0], item[1], item[2], item[3], item[4], cat_l, cat_m, cat_s, due))
            
    conn.commit()
    conn.close()

# --- 라우트 및 REST API ---

@app.route('/')
def index():
    return render_template('index.html')

# 1. 행사 목록 조회
@app.route('/api/events', methods=['GET'])
def get_events():
    conn = get_db_connection()
    events = conn.execute('SELECT * FROM events ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in events])

# 2. 신규 행사 등록
@app.route('/api/events', methods=['POST'])
def create_event():
    data = request.json
    title = data.get('title')
    event_date = data.get('event_date', '')
    description = data.get('description', '')
    copy_template = data.get('copy_template', False)
    template_id = data.get('template_id')

    if not title:
        return jsonify({'error': '행사명을 입력하세요.'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO events (title, event_date, description) VALUES (?, ?, ?)',
                   (title, event_date, description))
    new_event_id = cursor.lastrowid

    # If copy_template is true and template_id is not specified, set to 'default'
    if copy_template and not template_id:
        template_id = 'default'

    if template_id == 'default':
        # Copy from event_id = 1
        cursor.execute('''
            SELECT item_no, content, assignee, check_point, remark, category_large, category_medium, category_small, due_date 
            FROM checklists WHERE event_id = 1 ORDER BY item_no ASC
        ''')
        template_items = cursor.fetchall()
        for item in template_items:
            cursor.execute('''
                INSERT INTO checklists (event_id, item_no, content, assignee, check_point, remark, is_completed, category_large, category_medium, category_small, due_date)
                VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
            ''', (new_event_id, item['item_no'], item['content'], item['assignee'], item['check_point'], item['remark'],
                  item['category_large'], item['category_medium'], item['category_small'], item['due_date']))
    elif template_id and template_id != 'none':
        try:
            tid = int(template_id)
            cursor.execute('''
                SELECT item_no, content, assignee, check_point, remark, category_large, category_medium, category_small, due_date
                FROM template_items WHERE template_id = ? ORDER BY item_no ASC
            ''', (tid,))
            template_items = cursor.fetchall()
            for item in template_items:
                cursor.execute('''
                    INSERT INTO checklists (event_id, item_no, content, assignee, check_point, remark, is_completed, category_large, category_medium, category_small, due_date)
                    VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
                ''', (new_event_id, item['item_no'], item['content'], item['assignee'], item['check_point'], item['remark'],
                      item['category_large'], item['category_medium'], item['category_small'], item['due_date']))
        except ValueError:
            pass

    conn.commit()
    conn.close()
    return jsonify({'message': '행사가 생성되었습니다.', 'id': new_event_id}), 201

# --- 템플릿 관리 REST API ---

# 2-1. 템플릿 목록 조회
@app.route('/api/templates', methods=['GET'])
def get_templates():
    conn = get_db_connection()
    templates = conn.execute('SELECT * FROM event_templates ORDER BY name ASC').fetchall()
    conn.close()
    return jsonify([dict(tx) for tx in templates])

# 2-2. 특정 템플릿 상세 및 아이템 조회
@app.route('/api/templates/<int:template_id>', methods=['GET'])
def get_template_details(template_id):
    conn = get_db_connection()
    template = conn.execute('SELECT * FROM event_templates WHERE id = ?', (template_id,)).fetchone()
    if not template:
        conn.close()
        return jsonify({'error': '템플릿을 찾을 수 없습니다.'}), 404
    
    items = conn.execute('SELECT * FROM template_items WHERE template_id = ? ORDER BY item_no ASC', (template_id,)).fetchall()
    conn.close()
    
    res = dict(template)
    res['items'] = [dict(ix) for ix in items]
    return jsonify(res)

# 2-3. 템플릿 등록 및 수정
@app.route('/api/templates', methods=['POST'])
def save_template():
    data = request.json
    name = data.get('name')
    items = data.get('items', [])
    
    if not name:
        return jsonify({'error': '템플릿 이름을 입력하세요.'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 동일한 이름의 템플릿이 이미 존재하는지 확인
        cursor.execute('SELECT id FROM event_templates WHERE name = ?', (name,))
        row = cursor.fetchone()
        if row:
            template_id = row['id']
            # 기존 템플릿 아이템 전체 삭제
            cursor.execute('DELETE FROM template_items WHERE template_id = ?', (template_id,))
        else:
            # 신규 템플릿 생성
            cursor.execute('INSERT INTO event_templates (name) VALUES (?)', (name,))
            template_id = cursor.lastrowid
            
        # 신규 아이템들 일괄 등록
        for idx, item in enumerate(items):
            cursor.execute('''
                INSERT INTO template_items (template_id, item_no, category_large, category_medium, category_small, content, assignee, check_point, remark, due_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                template_id,
                idx + 1,
                item.get('category_large', ''),
                item.get('category_medium', ''),
                item.get('category_small', ''),
                item.get('content', ''),
                item.get('assignee', ''),
                item.get('check_point', ''),
                item.get('remark', ''),
                item.get('due_date', '')
            ))
        conn.commit()
        return jsonify({'message': '템플릿이 성공적으로 저장되었습니다.', 'id': template_id}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# 2-4. 템플릿 삭제
@app.route('/api/templates/<int:template_id>', methods=['DELETE'])
def delete_template(template_id):
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM event_templates WHERE id = ?', (template_id,))
        conn.commit()
        return jsonify({'message': '템플릿이 삭제되었습니다.'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# 3. 특정 행사의 체크리스트 조회
@app.route('/api/events/<int:event_id>/checklists', methods=['GET'])
def get_checklists(event_id):
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM checklists WHERE event_id = ? ORDER BY item_no ASC', (event_id,)).fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in items])

# 4. 체크리스트 항목 추가
@app.route('/api/events/<int:event_id>/checklists', methods=['POST'])
def add_checklist_item(event_id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 마지막 NO 번호 자동 계산
    cursor.execute('SELECT MAX(item_no) FROM checklists WHERE event_id = ?', (event_id,))
    max_no = cursor.fetchone()[0] or 0
    next_no = max_no + 1

    cursor.execute('''
        INSERT INTO checklists (event_id, item_no, content, assignee, check_point, remark, category_large, category_medium, category_small, due_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (event_id, next_no, 
          data.get('content', ''), 
          data.get('assignee', ''), 
          data.get('check_point', ''), 
          data.get('remark', ''),
          data.get('category_large', ''),
          data.get('category_medium', ''),
          data.get('category_small', ''),
          data.get('due_date', '')))
    
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return jsonify({'message': '항목이 추가되었습니다.', 'id': new_id, 'item_no': next_no}), 201

# 4-1. 체크리스트 항목 수정 (PUT)
@app.route('/api/checklists/<int:item_id>', methods=['PUT'])
def update_checklist_item(item_id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE checklists 
        SET content = ?, assignee = ?, check_point = ?, remark = ?,
            category_large = ?, category_medium = ?, category_small = ?, due_date = ?
        WHERE id = ?
    ''', (
        data.get('content', ''),
        data.get('assignee', ''),
        data.get('check_point', ''),
        data.get('remark', ''),
        data.get('category_large', ''),
        data.get('category_medium', ''),
        data.get('category_small', ''),
        data.get('due_date', ''),
        item_id
    ))
    conn.commit()
    conn.close()
    return jsonify({'message': '항목이 성공적으로 수정되었습니다.'})

# 5. 체크리스트 완료 상태 토글
@app.route('/api/checklists/<int:item_id>/toggle', methods=['POST'])
def toggle_checklist(item_id):
    data = request.json
    is_completed = 1 if data.get('is_completed') else 0
    
    conn = get_db_connection()
    conn.execute('UPDATE checklists SET is_completed = ? WHERE id = ?', (is_completed, item_id))
    conn.commit()
    conn.close()
    return jsonify({'message': '상태가 업데이트되었습니다.', 'is_completed': is_completed})

# 6. 체크리스트 항목 삭제
@app.route('/api/checklists/<int:item_id>', methods=['DELETE'])
def delete_checklist_item(item_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM checklists WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': '항목이 삭제되었습니다.'})

# 7. 헬스체크 API
@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
