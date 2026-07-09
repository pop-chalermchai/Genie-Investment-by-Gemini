"""Admin/user role separation.

Research authoring and the shared thai_funds sync are admin-only; admin-authored
reports are readable by every user. Regular users keep full control of their own
portfolio data (covered by test_auth_isolation.py).
"""
import sqlite3

from conftest import auth_headers

ADMIN = "role-admin-user"
USER = "role-regular-user"

REPORT = {
    "report_key": "role-test-report",
    "ticker": "NVDA",
    "company_name": "Nvidia Corp",
    "en_overview": "> **RECOMMENDATION: BUY**\n\nAdmin-authored content.",
}


def _promote_to_admin(db_path, user_id):
    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO profiles (user_id, role) VALUES (?, 'admin')", (user_id,))
    conn.commit()
    conn.close()


def test_regular_user_cannot_author_research(multiuser_db):
    c, _, _ = multiuser_db
    assert c.post('/api/research-report', json=REPORT, headers=auth_headers(USER)).status_code == 403
    assert c.put('/api/research-report?key=x', json=REPORT, headers=auth_headers(USER)).status_code == 403
    assert c.delete('/api/research-report?key=x', headers=auth_headers(USER)).status_code == 403


def test_regular_user_cannot_trigger_shared_fund_sync(multiuser_db):
    c, _, _ = multiuser_db
    assert c.post('/api/thai-fund/sync', headers=auth_headers(USER)).status_code == 403


def test_admin_can_author_and_every_user_can_read(multiuser_db):
    c, _, db_path = multiuser_db
    _promote_to_admin(db_path, ADMIN)

    r = c.post('/api/research-report', json=REPORT, headers=auth_headers(ADMIN))
    assert r.status_code == 200, r.get_json()

    # The admin's report is published read-only to a regular user…
    reports = c.get('/api/reports', headers=auth_headers(USER)).get_json()
    assert "role-test-report" in reports

    # …but that user still can't modify or delete it.
    assert c.put('/api/research-report?key=role-test-report', json=REPORT,
                 headers=auth_headers(USER)).status_code == 403
    assert c.delete('/api/research-report?key=role-test-report',
                    headers=auth_headers(USER)).status_code == 403

    # The admin can delete their own report.
    assert c.delete('/api/research-report?key=role-test-report',
                    headers=auth_headers(ADMIN)).status_code == 200


def test_profile_reports_role(multiuser_db):
    c, _, db_path = multiuser_db
    _promote_to_admin(db_path, ADMIN)
    assert c.get('/api/profile', headers=auth_headers(ADMIN)).get_json()['role'] == 'admin'
    assert c.get('/api/profile', headers=auth_headers(USER)).get_json()['role'] == 'user'
