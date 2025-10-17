"""
Nocturnal Archive Developer Dashboard
Real-time monitoring and analytics for beta deployment
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List
import sqlite3

app = Flask(__name__)
CORS(app)

class DashboardAnalytics:
    """Analytics engine for the dashboard"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(Path.home() / ".nocturnal_archive" / "analytics.db")
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                license_key TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP,
                total_queries INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active'
            )
        """)
        
        # Queries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                query_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                query_text TEXT,
                tools_used TEXT,
                tokens_used INTEGER,
                response_time REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Usage stats table (daily aggregates)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                date DATE PRIMARY KEY,
                total_users INTEGER,
                active_users INTEGER,
                total_queries INTEGER,
                total_tokens INTEGER,
                avg_response_time REAL
            )
        """)
        
        # Errors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS errors (
                error_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                error_type TEXT,
                error_message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def record_query(self, user_id: str, query: str, tools: List[str], 
                    tokens: int, response_time: float):
        """Record a query"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Ensure user exists (create if not)
        cursor.execute("""
            INSERT OR IGNORE INTO users (user_id, email, total_queries, total_tokens)
            VALUES (?, ?, 0, 0)
        """, (user_id, f"{user_id}@unknown.dev"))
        
        cursor.execute("""
            INSERT INTO queries (user_id, query_text, tools_used, tokens_used, response_time)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, query, json.dumps(tools), tokens, response_time))
        
        # Update user stats
        cursor.execute("""
            UPDATE users 
            SET last_active = CURRENT_TIMESTAMP,
                total_queries = total_queries + 1,
                total_tokens = total_tokens + ?
            WHERE user_id = ?
        """, (tokens, user_id))
        
        conn.commit()
        conn.close()
    
    def get_overview_stats(self) -> Dict:
        """Get overview statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total users
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        # Active users (last 24h)
        cursor.execute("""
            SELECT COUNT(*) FROM users 
            WHERE last_active > datetime('now', '-1 day')
        """)
        active_users = cursor.fetchone()[0]
        
        # Today's queries
        cursor.execute("""
            SELECT COUNT(*), SUM(tokens_used), AVG(response_time)
            FROM queries 
            WHERE DATE(timestamp) = DATE('now')
        """)
        today_queries, today_tokens, avg_response = cursor.fetchone()
        
        # Total queries
        cursor.execute("SELECT COUNT(*), SUM(tokens_used) FROM queries")
        total_queries, total_tokens = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_users': total_users,
            'active_users_24h': active_users,
            'today_queries': today_queries or 0,
            'today_tokens': today_tokens or 0,
            'total_queries': total_queries or 0,
            'total_tokens': total_tokens or 0,
            'avg_response_time': round(avg_response or 0, 2)
        }
    
    def get_user_list(self) -> List[Dict]:
        """Get list of all users with stats"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, email, created_at, last_active, 
                   total_queries, total_tokens, status
            FROM users
            ORDER BY last_active DESC
        """)
        
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return users
    
    def get_query_history(self, limit: int = 100) -> List[Dict]:
        """Get recent query history"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT q.*, u.email
            FROM queries q
            JOIN users u ON q.user_id = u.user_id
            ORDER BY q.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        queries = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return queries
    
    def get_usage_trends(self, days: int = 7) -> Dict:
        """Get usage trends over time"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DATE(timestamp) as date, 
                   COUNT(*) as queries,
                   SUM(tokens_used) as tokens
            FROM queries
            WHERE timestamp > datetime('now', '-' || ? || ' days')
            GROUP BY DATE(timestamp)
            ORDER BY date
        """, (days,))
        
        trends = {
            'dates': [],
            'queries': [],
            'tokens': []
        }
        
        for row in cursor.fetchall():
            trends['dates'].append(row[0])
            trends['queries'].append(row[1])
            trends['tokens'].append(row[2])
        
        conn.close()
        return trends
    
    def kill_switch(self, reason: str = "Emergency shutdown"):
        """Activate kill switch - disable all users"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users SET status = 'disabled'
            WHERE status = 'active'
        """)
        
        # Log the kill switch activation
        cursor.execute("""
            INSERT INTO errors (user_id, error_type, error_message)
            VALUES ('SYSTEM', 'KILL_SWITCH', ?)
        """, (reason,))
        
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        
        return affected
    
    def reactivate_users(self):
        """Reactivate all users"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users SET status = 'active'
            WHERE status = 'disabled'
        """)
        
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        
        return affected


# Initialize analytics
analytics = DashboardAnalytics()

# Routes
@app.route('/')
def index():
    """Dashboard home page"""
    return render_template('dashboard.html')

@app.route('/api/overview')
def api_overview():
    """Get overview statistics"""
    return jsonify(analytics.get_overview_stats())

@app.route('/api/users')
def api_users():
    """Get user list"""
    return jsonify(analytics.get_user_list())

@app.route('/api/queries')
def api_queries():
    """Get query history"""
    limit = request.args.get('limit', 100, type=int)
    return jsonify(analytics.get_query_history(limit))

@app.route('/api/trends')
def api_trends():
    """Get usage trends"""
    days = request.args.get('days', 7, type=int)
    return jsonify(analytics.get_usage_trends(days))

@app.route('/api/kill-switch', methods=['POST'])
def api_kill_switch():
    """Activate kill switch"""
    data = request.get_json()
    reason = data.get('reason', 'Emergency shutdown')
    
    # Verify admin password
    admin_password = data.get('admin_password')
    if admin_password != os.getenv('NOCTURNAL_ADMIN_PASSWORD', 'admin123'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    affected = analytics.kill_switch(reason)
    return jsonify({
        'success': True,
        'affected_users': affected,
        'message': f'Kill switch activated. {affected} users disabled.'
    })

@app.route('/api/reactivate', methods=['POST'])
def api_reactivate():
    """Reactivate all users"""
    data = request.get_json()
    
    # Verify admin password
    admin_password = data.get('admin_password')
    if admin_password != os.getenv('NOCTURNAL_ADMIN_PASSWORD', 'admin123'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    affected = analytics.reactivate_users()
    return jsonify({
        'success': True,
        'affected_users': affected,
        'message': f'{affected} users reactivated.'
    })


def run_dashboard(host='0.0.0.0', port=5000, debug=False):
    """Run the dashboard server"""
    print(f"🚀 Nocturnal Archive Developer Dashboard")
    print(f"📊 Dashboard: http://localhost:{port}")
    print(f"🔒 Admin password: {os.getenv('NOCTURNAL_ADMIN_PASSWORD', 'admin123')}")
    print()
    
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_dashboard(debug=True)
