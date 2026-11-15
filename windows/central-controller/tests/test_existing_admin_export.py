from __future__ import annotations
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from export_existing_admin_schedule import export
from existing_admin_sessions import ExistingAdminSessions

class ExportTests(unittest.TestCase):
    def test_safe_export_contains_only_schedule(self):
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/'original.sqlite3'
            dst=Path(td)/'export.sqlite3'
            with sqlite3.connect(src) as db:
                db.execute('''CREATE TABLE sessions(session_id TEXT PRIMARY KEY,
                    faculty_id TEXT,course TEXT,subject TEXT,topic TEXT,
                    starts_at INTEGER,ends_at INTEGER,meeting_id TEXT,meeting_passcode TEXT)''')
                db.execute("INSERT INTO sessions VALUES ('s1','fac1','Medicine','Cardiology','Topic',1800000000,1800003600,'98765432101','secret-passcode')")
            self.assertEqual(export(src,dst),1)
            self.assertEqual(ExistingAdminSessions(dst).snapshot()['sessions'][0]['topic'],'Topic')
            raw=dst.read_bytes()
            self.assertNotIn(b'98765432101',raw)
            self.assertNotIn(b'secret-passcode',raw)
            self.assertIn(b'Topic',raw)
    def test_does_not_overwrite_original(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'same.db';f.write_bytes(b'original')
            with self.assertRaises(ValueError):export(f,f)
            self.assertEqual(f.read_bytes(),b'original')

if __name__=='__main__':unittest.main()
