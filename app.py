from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file, abort
import pg8000
import bcrypt
import os
from datetime import datetime
import pandas as pd
import numpy as np
from catboost import CatBoostClassifier
from collections import defaultdict
import io
import csv

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Load the CatBoost model
def load_model():
    """Load the trained CatBoost model"""
    try:
        model = CatBoostClassifier()
        model.load_model('catboost.cbm')
        print(f"CatBoost model loaded successfully!")
        print(f"Model feature names: {model.feature_names_}")
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        return None

# Initialize model
model = load_model()

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'churn_sys_db',
    'user': 'postgres',
    'password': 'BQArts1280',
    'port': '5432'
}

# Fallback user system (in-memory) for when database is not available
FALLBACK_USERS = {
    'admin': {
        'password': 'admin123',
        'email': 'admin@example.com',
        'user_id': 1
    },
    'demo': {
        'password': 'demo123',
        'email': 'demo@example.com',
        'user_id': 2
    }
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = pg8000.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def create_tables():
    """Create necessary tables if they don't exist and add missing columns"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    first_name VARCHAR(50),
                    last_name VARCHAR(50),
                    role VARCHAR(20) DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            """)
            
            # Ensure new columns exist (for upgrades)
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(50);")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR(50);")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user';")
            
            # Create predictions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    regularity FLOAT,
                    revenue FLOAT,
                    average_revenue_per_user FLOAT,
                    frequence FLOAT,
                    data_volume FLOAT,
                    frequence_rech FLOAT,
                    total_amount_spent FLOAT,
                    prediction INTEGER,
                    confidence INTEGER,
                    churn_status VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create a default admin user if no users exist
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            if user_count == 0:
                # Create default admin user
                admin_password = "admin123"
                password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
                
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash)
                    VALUES (%s, %s, %s)
                """, ('admin', 'admin@example.com', password_hash.decode('utf-8')))
                
                print("Default admin user created:")
                print("Username: admin")
                print("Password: admin123")
            
            # Add sample predictions data if none exists
            cursor.execute("SELECT COUNT(*) FROM predictions")
            prediction_count = cursor.fetchone()[0]
            
            if prediction_count == 0:
                # Get admin user ID
                cursor.execute("SELECT id FROM users WHERE username = 'admin'")
                admin_id = cursor.fetchone()[0]
                
                # Insert sample predictions data
                sample_data = [
                    # Format: (user_id, regularity, revenue, avg_revenue_per_user, frequence, data_volume, frequence_rech, total_amount_spent, prediction, confidence, churn_status)
                    (admin_id, 0.8, 1500.0, 75.0, 12.0, 500.0, 8.0, 2000.0, 0, 85, 'stayed'),
                    (admin_id, 0.3, 800.0, 40.0, 5.0, 200.0, 3.0, 1200.0, 1, 92, 'churned'),
                    (admin_id, 0.9, 2000.0, 100.0, 15.0, 800.0, 12.0, 3000.0, 0, 78, 'stayed'),
                    (admin_id, 0.2, 600.0, 30.0, 3.0, 150.0, 2.0, 800.0, 1, 95, 'churned'),
                    (admin_id, 0.7, 1200.0, 60.0, 10.0, 400.0, 7.0, 1800.0, 0, 82, 'stayed'),
                    (admin_id, 0.4, 900.0, 45.0, 6.0, 250.0, 4.0, 1400.0, 1, 88, 'churned'),
                    (admin_id, 0.6, 1100.0, 55.0, 9.0, 350.0, 6.0, 1600.0, 0, 79, 'stayed'),
                    (admin_id, 0.1, 500.0, 25.0, 2.0, 100.0, 1.0, 600.0, 1, 96, 'churned'),
                    (admin_id, 0.85, 1800.0, 90.0, 14.0, 700.0, 11.0, 2800.0, 0, 81, 'stayed'),
                    (admin_id, 0.25, 700.0, 35.0, 4.0, 180.0, 2.5, 1000.0, 1, 90, 'churned'),
                ]
                
                cursor.executemany("""
                    INSERT INTO predictions (user_id, regularity, revenue, average_revenue_per_user, frequence, data_volume, frequence_rech, total_amount_spent, prediction, confidence, churn_status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW() - INTERVAL '%s days')
                """, [(data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9], data[10], i) for i, data in enumerate(sample_data)])
                
                print(f"Added {len(sample_data)} sample predictions for testing analytics!")
            
            conn.commit()
            cursor.close()
            conn.close()
            print("Database tables created successfully!")
            
        except Exception as e:
            print(f"Error creating tables: {e}")
            conn.rollback()
            conn.close()

@app.route('/')
def index():
    """Redirect to login page"""
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login form"""
    error = None
    success = None
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Try database first
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
                
                if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
                    # Update last login time
                    cursor.execute("UPDATE users SET last_login = %s WHERE id = %s", 
                                 (datetime.now(), user[0]))
                    conn.commit()
                    
                    # Store user info in session
                    session['user_id'] = user[0]
                    session['username'] = user[1]
                    session['email'] = user[2]
                    flash('Successfully logged in!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    error = 'Invalid username or password!'
                
                cursor.close()
                conn.close()
                
            except Exception as e:
                error = f'Database error: {e}'
                conn.close()
        else:
            # Fallback to in-memory users
            if username in FALLBACK_USERS and FALLBACK_USERS[username]['password'] == password:
                session['user_id'] = FALLBACK_USERS[username]['user_id']
                session['username'] = username
                session['email'] = FALLBACK_USERS[username]['email']
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid username or password!'
    
    return render_template('login.html', error=error, success=success)

@app.route('/dashboard')
def dashboard():
    """Dashboard page - only accessible after login"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', user=session)

# Dashboard API endpoints for real-time data
@app.route('/api/dashboard/quick-stats')
def api_dashboard_quick_stats():
    """Get real-time quick stats for dashboard"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Today's predictions
        cursor.execute("""
            SELECT COUNT(*) FROM predictions 
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        today_predictions = cursor.fetchone()[0]
        
        # Yesterday's predictions for comparison
        cursor.execute("""
            SELECT COUNT(*) FROM predictions 
            WHERE DATE(created_at) = CURRENT_DATE - INTERVAL '1 day'
        """)
        yesterday_predictions = cursor.fetchone()[0]
        
        # High risk customers (churn prediction = 1) today
        cursor.execute("""
            SELECT COUNT(*) FROM predictions 
            WHERE DATE(created_at) = CURRENT_DATE AND prediction = 1
        """)
        high_risk_today = cursor.fetchone()[0]
        
        # High risk customers yesterday
        cursor.execute("""
            SELECT COUNT(*) FROM predictions 
            WHERE DATE(created_at) = CURRENT_DATE - INTERVAL '1 day' AND prediction = 1
        """)
        high_risk_yesterday = cursor.fetchone()[0]
        
        # Model accuracy (based on confidence scores)
        cursor.execute("""
            SELECT AVG(confidence) FROM predictions 
            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
        """)
        avg_confidence = cursor.fetchone()[0] or 94.2
        
        # Calculate percentage changes
        predictions_change = 0
        if yesterday_predictions > 0:
            predictions_change = ((today_predictions - yesterday_predictions) / yesterday_predictions) * 100
        
        high_risk_change = 0
        if high_risk_yesterday > 0:
            high_risk_change = ((high_risk_today - high_risk_yesterday) / high_risk_yesterday) * 100
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'today_predictions': today_predictions,
            'predictions_change': round(predictions_change, 1),
            'high_risk_count': high_risk_today,
            'high_risk_change': round(high_risk_change, 1),
            'model_accuracy': round(avg_confidence, 1),
            'avg_response_time': 0.8  # This could be calculated from actual response times
        })
        
    except Exception as e:
        print(f"Dashboard quick stats error: {e}")
        if conn:
            conn.rollback()
        return jsonify({'error': 'Failed to fetch quick stats'}), 500

@app.route('/api/dashboard/recent-activity')
def api_dashboard_recent_activity():
    """Get recent activity feed for dashboard"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Get recent predictions with user info
        cursor.execute("""
            SELECT p.created_at, p.churn_status, p.confidence, u.username
            FROM predictions p
            JOIN users u ON p.user_id = u.id
            ORDER BY p.created_at DESC
            LIMIT 10
        """)
        
        activities = []
        for row in cursor.fetchall():
            created_at, churn_status, confidence, username = row
            
            # Calculate time ago
            time_diff = datetime.now() - created_at
            if time_diff.total_seconds() < 60:
                time_ago = "Just now"
            elif time_diff.total_seconds() < 3600:
                minutes = int(time_diff.total_seconds() // 60)
                time_ago = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            elif time_diff.total_seconds() < 86400:
                hours = int(time_diff.total_seconds() // 3600)
                time_ago = f"{hours} hour{'s' if hours != 1 else ''} ago"
            else:
                days = int(time_diff.total_seconds() // 86400)
                time_ago = f"{days} day{'s' if days != 1 else ''} ago"
            
            # Determine status and icon
            if churn_status == "HIGH CHURN RISK":
                status = "high-risk"
                icon = "fa-exclamation-triangle"
                title = "High risk prediction"
                desc = f"Customer predicted to churn (Confidence: {confidence}%)"
            else:
                status = "success"
                icon = "fa-check-circle"
                title = "Low risk prediction"
                desc = f"Customer predicted to stay (Confidence: {confidence}%)"
            
            activities.append({
                'title': title,
                'desc': desc,
                'time': time_ago,
                'status': status,
                'icon': icon,
                'username': username
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({'activities': activities})
        
    except Exception as e:
        print(f"Dashboard activity error: {e}")
        if conn:
            conn.rollback()
        return jsonify({'error': 'Failed to fetch recent activity'}), 500

@app.route('/api/dashboard/system-status')
def api_dashboard_system_status():
    """Get system status information"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Check if model is loaded
        model_status = "Operational" if model is not None else "Error"
        model_active = model is not None
        
        # Check database connection
        conn = get_db_connection()
        db_status = "Connected" if conn else "Disconnected"
        db_online = conn is not None
        if conn:
            conn.close()
        
        # Calculate uptime (simplified - could be enhanced with actual uptime tracking)
        uptime_percentage = 99.9
        
        return jsonify({
            'ml_model': {
                'status': model_status,
                'active': model_active
            },
            'database': {
                'status': db_status,
                'online': db_online
            },
            'security': {
                'status': 'Protected',
                'secure': True
            },
            'uptime': {
                'percentage': uptime_percentage,
                'stable': True
            }
        })
        
    except Exception as e:
        print(f"System status error: {e}")
        return jsonify({'error': 'Failed to fetch system status'}), 500

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/predict')
def predict_page():
    """Prediction page - only accessible after login"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('predict.html')

@app.route('/predict', methods=['POST'])
def predict():
    """Handle prediction request"""
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first!'}), 401
    
    if model is None:
        return jsonify({'error': 'Model not loaded!'}), 500
    
    try:
        # Get form data for the actual model features
        data = {
            'REGULARITY': float(request.form['REGULARITY']),
            'REVENUE': float(request.form['REVENUE']),
            'AVERAGE_REVENUE_PER_USER': float(request.form['AVERAGE_REVENUE_PER_USER']),
            'FREQUENCE': float(request.form['FREQUENCE']),
            'DATA_VOLUME': float(request.form['DATA_VOLUME']),
            'FREQUENCE_RECH': float(request.form['FREQUENCE_RECH']),
            'TOTAL_AMOUNT_SPENT': float(request.form['TOTAL_AMOUNT_SPENT'])
        }
        
        # Create DataFrame with the expected feature names
        df = pd.DataFrame([data])
        
        # Make prediction using the CatBoost model
        prediction = model.predict(df)[0]
        proba = model.predict_proba(df)[0]
        confidence = int(100 * max(proba))
        churn_status = "HIGH CHURN RISK" if prediction == 1 else "LOW CHURN RISK"

        # Store prediction in the database
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO predictions (
                        user_id, regularity, revenue, average_revenue_per_user, frequence, data_volume, frequence_rech, total_amount_spent, prediction, confidence, churn_status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    session['user_id'],
                    data['REGULARITY'],
                    data['REVENUE'],
                    data['AVERAGE_REVENUE_PER_USER'],
                    data['FREQUENCE'],
                    data['DATA_VOLUME'],
                    data['FREQUENCE_RECH'],
                    data['TOTAL_AMOUNT_SPENT'],
                    int(prediction),
                    confidence,
                    churn_status
                ))
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as e:
                print(f"Error saving prediction: {e}")
                if conn:
                    conn.rollback()
        
        return jsonify({
            'success': True,
            'prediction': int(prediction),
            'confidence': confidence,
            'message': f"Customer is {'likely to churn' if prediction == 1 else 'likely to stay'}."
        })
        
    except Exception as e:
        return jsonify({'error': f'Prediction error: {str(e)}'}), 500

@app.route('/profile')
def user_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('user_profile.html', user=session)

@app.route('/analytics')
def analytics():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('analytics.html', user=session)

# Analytics API endpoint
@app.route('/api/analytics')
def api_analytics():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    try:
        cursor = conn.cursor()
        # Group by date and prediction (1=churn, 0=stay)
        cursor.execute('''
            SELECT DATE(created_at) as day, prediction, COUNT(*)
            FROM predictions
            GROUP BY day, prediction
            ORDER BY day ASC
        ''')
        rows = cursor.fetchall()
        # Build date-indexed dicts
        churn_counts = defaultdict(int)
        stay_counts = defaultdict(int)
        all_dates = set()
        for day, prediction, count in rows:
            day_str = str(day)
            all_dates.add(day_str)
            if prediction == 1:
                churn_counts[day_str] = count
            else:
                stay_counts[day_str] = count
        # Sort dates
        sorted_dates = sorted(all_dates)
        churn = [churn_counts.get(d, 0) for d in sorted_dates]
        stay = [stay_counts.get(d, 0) for d in sorted_dates]
        cursor.close()
        conn.close()
        return jsonify({'labels': sorted_dates, 'churn': churn, 'stay': stay})
    except Exception as e:
        print(f"Analytics error: {e}")
        if conn:
            conn.rollback()
        return jsonify({'error': 'Failed to fetch analytics'}), 500

# Summary statistics API
@app.route('/api/analytics/summary')
def api_analytics_summary():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    
    # Get filter parameters
    days = request.args.get('days', type=int)
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    
    # Build WHERE clause
    where_clause = ""
    params = []
    
    if days:
        where_clause = "WHERE created_at >= NOW() - INTERVAL '%s days'"
        params.append(days)
    elif date_from and date_to:
        where_clause = "WHERE created_at >= %s AND created_at <= %s"
        params.extend([date_from, date_to])
    
    try:
        cursor = conn.cursor()
        
        # Main query with filters
        query = f"SELECT COUNT(*), SUM(CASE WHEN prediction=1 THEN 1 ELSE 0 END), AVG(revenue), AVG(regularity), AVG(data_volume) FROM predictions {where_clause}"
        cursor.execute(query, params)
        total, churned, avg_revenue, avg_regularity, avg_data_volume = cursor.fetchone()
        churn_rate = (churned / total * 100) if total else 0
        
        # Calculate changes from previous period
        if days:
            # Compare with previous period of same length
            prev_query = f"SELECT COUNT(*), SUM(CASE WHEN prediction=1 THEN 1 ELSE 0 END), AVG(revenue) FROM predictions WHERE created_at >= NOW() - INTERVAL '{days*2} days' AND created_at < NOW() - INTERVAL '{days} days'"
            cursor.execute(prev_query)
            prev_total, prev_churned, prev_avg_revenue = cursor.fetchone()
            
            total_change = ((total - prev_total) / prev_total * 100) if prev_total else 0
            churn_rate_change = ((churn_rate - (prev_churned / prev_total * 100)) if prev_total and prev_churned else 0)
            revenue_change = ((avg_revenue - prev_avg_revenue) / prev_avg_revenue * 100) if prev_avg_revenue else 0
            accuracy_change = 0.8  # Placeholder for model accuracy change
        else:
            total_change = churn_rate_change = revenue_change = accuracy_change = 0
        
        # Calculate additional metrics
        cursor.execute(f"""
            SELECT 
                AVG(confidence) as avg_confidence,
                COUNT(CASE WHEN confidence >= 80 THEN 1 END) as high_confidence_count,
                COUNT(CASE WHEN confidence < 80 THEN 1 END) as low_confidence_count
            FROM predictions {where_clause}
        """, params)
        avg_confidence, high_confidence_count, low_confidence_count = cursor.fetchone()
        
        # Calculate model accuracy based on confidence scores (simplified)
        model_accuracy = avg_confidence or 85.0
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'total': total or 0,
            'churned': churned or 0,
            'churn_rate': churn_rate,
            'avg_revenue': avg_revenue or 0,
            'avg_regularity': avg_regularity or 0,
            'avg_data_volume': avg_data_volume or 0,
            'model_accuracy': model_accuracy,
            'avg_confidence': avg_confidence or 0,
            'high_confidence_count': high_confidence_count or 0,
            'low_confidence_count': low_confidence_count or 0,
            'total_change': total_change,
            'churn_rate_change': churn_rate_change,
            'revenue_change': revenue_change,
            'accuracy_change': accuracy_change
        })
    except Exception as e:
        print(f"Summary analytics error: {e}")
        if conn:
            conn.rollback()
        return jsonify({'error': 'Failed to fetch summary analytics'}), 500

# Churn pie chart API
@app.route('/api/analytics/pie')
def api_analytics_pie():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    
    # Get filter parameters
    days = request.args.get('days', type=int)
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    
    # Build WHERE clause
    where_clause = ""
    params = []
    
    if days:
        where_clause = "WHERE created_at >= NOW() - INTERVAL '%s days'"
        params.append(days)
    elif date_from and date_to:
        where_clause = "WHERE created_at >= %s AND created_at <= %s"
        params.extend([date_from, date_to])
    
    try:
        cursor = conn.cursor()
        query = f"SELECT prediction, COUNT(*) FROM predictions {where_clause} GROUP BY prediction"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        churned = 0
        stayed = 0
        for prediction, count in rows:
            if prediction == 1:
                churned = count
            else:
                stayed = count
        cursor.close()
        conn.close()
        return jsonify({'churned': churned, 'stayed': stayed})
    except Exception as e:
        print(f"Pie analytics error: {e}")
        if conn:
            conn.rollback()
        return jsonify({'error': 'Failed to fetch pie analytics'}), 500

# Feature averages for churned vs. stay (bar chart)
@app.route('/api/analytics/feature-averages')
def api_analytics_feature_averages():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    
    # Get filter parameters
    days = request.args.get('days', type=int)
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    
    # Build WHERE clause
    where_clause = ""
    params = []
    
    if days:
        where_clause = "WHERE created_at >= NOW() - INTERVAL '%s days'"
        params.append(days)
    elif date_from and date_to:
        where_clause = "WHERE created_at >= %s AND created_at <= %s"
        params.extend([date_from, date_to])
    
    try:
        cursor = conn.cursor()
        query = f'''
            SELECT prediction,
                   AVG(revenue),
                   AVG(regularity),
                   AVG(data_volume),
                   AVG(average_revenue_per_user),
                   AVG(frequence),
                   AVG(frequence_rech),
                   AVG(total_amount_spent)
            FROM predictions
            {where_clause}
            GROUP BY prediction
        '''
        cursor.execute(query, params)
        rows = cursor.fetchall()
        data = {'churned': {}, 'stayed': {}}
        for row in rows:
            pred = 'churned' if row[0] == 1 else 'stayed'
            data[pred] = {
                'revenue': row[1] or 0,
                'regularity': row[2] or 0,
                'data_volume': row[3] or 0,
                'average_revenue_per_user': row[4] or 0,
                'frequence': row[5] or 0,
                'frequence_rech': row[6] or 0,
                'total_amount_spent': row[7] or 0
            }
        cursor.close()
        conn.close()
        return jsonify(data)
    except Exception as e:
        print(f"Feature averages analytics error: {e}")
        if conn:
            conn.rollback()
        return jsonify({'error': 'Failed to fetch feature averages'}), 500

# Feature importance API
@app.route('/api/analytics/feature-importance')
def api_analytics_feature_importance():
    try:
        # Feature names in the order they appear in the model
        features = ['REGULARITY', 'REVENUE', 'AVERAGE_REVENUE_PER_USER', 'FREQUENCE', 'DATA_VOLUME', 'FREQUENCE_RECH', 'TOTAL_AMOUNT_SPENT']
        feature_labels = ['Regularity', 'Revenue', 'Avg Revenue/User', 'Frequency', 'Data Volume', 'Recharge Freq', 'Total Spent']
        
        if model is not None:
            try:
                # Try to get feature importance from the model
                if hasattr(model, 'get_feature_importance'):
                    importances = model.get_feature_importance()
                    if len(importances) == len(features):
                        # Normalize importances to sum to 1
                        total_importance = sum(importances)
                        if total_importance > 0:
                            normalized_importances = [imp / total_importance for imp in importances]
                            return jsonify({'features': feature_labels, 'importances': normalized_importances})
                
                # If model doesn't have feature importance, calculate from database
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    
                    # Calculate correlation between each feature and churn prediction
                    correlations = []
                    for feature in features:
                        query = f"""
                            SELECT 
                                CORR({feature.lower()}, prediction::float) as correlation
                            FROM predictions
                            WHERE {feature.lower()} IS NOT NULL AND prediction IS NOT NULL
                        """
                        cursor.execute(query)
                        result = cursor.fetchone()
                        correlation = abs(result[0]) if result[0] is not None else 0
                        correlations.append(correlation)
                    
                    cursor.close()
                    conn.close()
                    
                    # Normalize correlations to sum to 1
                    total_correlation = sum(correlations)
                    if total_correlation > 0:
                        normalized_correlations = [corr / total_correlation for corr in correlations]
                        return jsonify({'features': feature_labels, 'importances': normalized_correlations})
            except Exception as model_error:
                print(f"Model feature importance error: {model_error}")
        
        # Fallback to sample data based on typical churn factors
        sample_importances = [0.25, 0.20, 0.15, 0.18, 0.12, 0.08, 0.02]  # Sample importance values
        return jsonify({'features': feature_labels, 'importances': sample_importances})
        
    except Exception as e:
        print(f"Feature importance analytics error: {e}")
        return jsonify({'error': 'Failed to fetch feature importance'}), 500

# Trend chart API for churn rate over time
@app.route('/api/analytics/trend')
def api_analytics_trend():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    
    # Get filter parameters
    days = request.args.get('days', type=int)
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    
    # Build WHERE clause
    where_clause = ""
    params = []
    
    if days:
        where_clause = "WHERE created_at >= NOW() - INTERVAL '%s days'"
        params.append(days)
    elif date_from and date_to:
        where_clause = "WHERE created_at >= %s AND created_at <= %s"
        params.extend([date_from, date_to])
    
    try:
        cursor = conn.cursor()
        
        # Get daily churn rates
        query = f"""
            SELECT 
                DATE(created_at) as day,
                COUNT(*) as total_predictions,
                SUM(CASE WHEN prediction = 1 THEN 1 ELSE 0 END) as churned_count
            FROM predictions
            {where_clause}
            GROUP BY DATE(created_at)
            ORDER BY day ASC
        """
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Process data for chart
        labels = []
        churn_rates = []
        
        for row in rows:
            day, total, churned = row
            if total > 0:
                churn_rate = (churned / total) * 100
                labels.append(day.strftime('%m/%d'))
                churn_rates.append(round(churn_rate, 1))
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'labels': labels,
            'churn_rates': churn_rates
        })
        
    except Exception as e:
        print(f"Trend analytics error: {e}")
        if conn:
            conn.rollback()
        return jsonify({'error': 'Failed to fetch trend data'}), 500

# Confidence distribution API
@app.route('/api/analytics/confidence-distribution')
def api_analytics_confidence_distribution():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    
    # Get filter parameters
    days = request.args.get('days', type=int)
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    
    # Build WHERE clause
    where_clause = ""
    params = []
    
    if days:
        where_clause = "WHERE created_at >= NOW() - INTERVAL '%s days'"
        params.append(days)
    elif date_from and date_to:
        where_clause = "WHERE created_at >= %s AND created_at <= %s"
        params.extend([date_from, date_to])
    
    try:
        cursor = conn.cursor()
        
        # Get confidence distribution
        query = f"""
            SELECT 
                CASE 
                    WHEN confidence >= 90 THEN '90-100%'
                    WHEN confidence >= 80 THEN '80-89%'
                    WHEN confidence >= 70 THEN '70-79%'
                    WHEN confidence >= 60 THEN '60-69%'
                    ELSE '50-59%'
                END as confidence_range,
                COUNT(*) as count
            FROM predictions
            {where_clause}
            GROUP BY confidence_range
            ORDER BY 
                CASE confidence_range
                    WHEN '90-100%' THEN 1
                    WHEN '80-89%' THEN 2
                    WHEN '70-79%' THEN 3
                    WHEN '60-69%' THEN 4
                    ELSE 5
                END
        """
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        labels = []
        counts = []
        
        for row in rows:
            confidence_range, count = row
            labels.append(confidence_range)
            counts.append(count)
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'labels': labels,
            'counts': counts
        })
        
    except Exception as e:
        print(f"Confidence distribution analytics error: {e}")
        if conn:
            conn.rollback()
        return jsonify({'error': 'Failed to fetch confidence distribution'}), 500

# Debug route to add sample data (remove in production)
@app.route('/api/debug/add-sample-data')
def api_debug_add_sample_data():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Get current user ID
        user_id = session['user_id']
        
        # Sample data with varied dates
        sample_data = [
            (user_id, 0.8, 1500.0, 75.0, 12.0, 500.0, 8.0, 2000.0, 0, 85, 'stayed'),
            (user_id, 0.3, 800.0, 40.0, 5.0, 200.0, 3.0, 1200.0, 1, 92, 'churned'),
            (user_id, 0.9, 2000.0, 100.0, 15.0, 800.0, 12.0, 3000.0, 0, 78, 'stayed'),
            (user_id, 0.2, 600.0, 30.0, 3.0, 150.0, 2.0, 800.0, 1, 95, 'churned'),
            (user_id, 0.7, 1200.0, 60.0, 10.0, 400.0, 7.0, 1800.0, 0, 82, 'stayed'),
        ]
        
        for i, data in enumerate(sample_data):
            cursor.execute("""
                INSERT INTO predictions (user_id, regularity, revenue, average_revenue_per_user, frequence, data_volume, frequence_rech, total_amount_spent, prediction, confidence, churn_status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW() - INTERVAL '%s days')
            """, (data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9], data[10], i))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': f'Added {len(sample_data)} sample predictions'})
    except Exception as e:
        print(f"Debug sample data error: {e}")
        if conn:
            conn.rollback()
        return jsonify({'error': 'Failed to add sample data'}), 500

# Reports page
@app.route('/reports')
def reports():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('reports.html', user=session)

# API to fetch predictions with filters and pagination
@app.route('/api/reports')
def api_reports():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    # Filters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    status = request.args.get('status')  # 'churned', 'stayed', or None
    user = request.args.get('user')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    offset = (page - 1) * page_size
    # Build query
    query = "SELECT p.id, u.username, p.regularity, p.revenue, p.average_revenue_per_user, p.frequence, p.data_volume, p.frequence_rech, p.total_amount_spent, p.prediction, p.confidence, p.churn_status, p.created_at FROM predictions p LEFT JOIN users u ON p.user_id = u.id WHERE 1=1"
    params = []
    if date_from:
        query += " AND p.created_at >= %s"
        params.append(date_from)
    if date_to:
        query += " AND p.created_at <= %s"
        params.append(date_to)
    if status == 'churned':
        query += " AND p.prediction = 1"
    elif status == 'stayed':
        query += " AND p.prediction = 0"
    if user:
        query += " AND u.username = %s"
        params.append(user)
    query += " ORDER BY p.created_at DESC LIMIT %s OFFSET %s"
    params.extend([page_size, offset])
    # Count query for pagination
    count_query = "SELECT COUNT(*) FROM predictions p LEFT JOIN users u ON p.user_id = u.id WHERE 1=1"
    count_params = []
    if date_from:
        count_query += " AND p.created_at >= %s"
        count_params.append(date_from)
    if date_to:
        count_query += " AND p.created_at <= %s"
        count_params.append(date_to)
    if status == 'churned':
        count_query += " AND p.prediction = 1"
    elif status == 'stayed':
        count_query += " AND p.prediction = 0"
    if user:
        count_query += " AND u.username = %s"
        count_params.append(user)
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        # Format results
        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'username': row[1],
                'regularity': row[2],
                'revenue': row[3],
                'average_revenue_per_user': row[4],
                'frequence': row[5],
                'data_volume': row[6],
                'frequence_rech': row[7],
                'total_amount_spent': row[8],
                'prediction': row[9],
                'confidence': row[10],
                'churn_status': row[11],
                'created_at': row[12].strftime('%Y-%m-%d %H:%M:%S') if row[12] else ''
            })
        return jsonify({'results': results, 'total': total})
    except Exception as e:
        print(f"Reports API error: {e}")
        if conn:
            conn.rollback()
        return jsonify({'error': 'Failed to fetch reports'}), 500

# API to download filtered predictions as CSV
@app.route('/api/reports/download')
def api_reports_download():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    # Same filters as above
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    status = request.args.get('status')
    user = request.args.get('user')
    query = "SELECT p.id, u.username, p.regularity, p.revenue, p.average_revenue_per_user, p.frequence, p.data_volume, p.frequence_rech, p.total_amount_spent, p.prediction, p.confidence, p.churn_status, p.created_at FROM predictions p LEFT JOIN users u ON p.user_id = u.id WHERE 1=1"
    params = []
    if date_from:
        query += " AND p.created_at >= %s"
        params.append(date_from)
    if date_to:
        query += " AND p.created_at <= %s"
        params.append(date_to)
    if status == 'churned':
        query += " AND p.prediction = 1"
    elif status == 'stayed':
        query += " AND p.prediction = 0"
    if user:
        query += " AND u.username = %s"
        params.append(user)
    query += " ORDER BY p.created_at DESC"
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        # Prepare CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Username', 'Regularity', 'Revenue', 'Avg Revenue/User', 'Frequency', 'Data Volume', 'Recharge Freq', 'Total Spent', 'Prediction', 'Confidence', 'Churn Status', 'Created At'])
        for row in rows:
            writer.writerow([
                row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12].strftime('%Y-%m-%d %H:%M:%S') if row[12] else ''
            ])
        output.seek(0)
        return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name='predictions_report.csv')
    except Exception as e:
        print(f"Reports Download API error: {e}")
        if conn:
            conn.rollback()
        return jsonify({'error': 'Failed to download report'}), 500

# API to delete a specific prediction report by ID
@app.route('/api/reports/delete', methods=['POST'])
def api_reports_delete():
    if 'user_id' not in session or session.get('username') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    report_id = data.get('id')
    if not report_id:
        return jsonify({'error': 'Report ID required'}), 400
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM predictions WHERE id=%s', (report_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Delete report error: {e}")
        if conn:
            conn.rollback()
        return jsonify({'error': 'Failed to delete report'}), 500

# Admin user management page
@app.route('/admin/users')
def admin_users():
    if 'user_id' not in session or session.get('username') != 'admin':
        abort(403)
    return render_template('admin_users.html', user=session)

# API for admin user management
@app.route('/api/admin/users', methods=['GET', 'POST', 'DELETE'])
def api_admin_users():
    if 'user_id' not in session or session.get('username') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    try:
        cursor = conn.cursor()
        if request.method == 'GET':
            cursor.execute('SELECT id, username, email, first_name, last_name, role, created_at FROM users ORDER BY id ASC')
            users = [
                {'id': row[0], 'username': row[1], 'email': row[2], 'first_name': row[3], 'last_name': row[4], 'role': row[5], 'created_at': row[6].strftime('%Y-%m-%d %H:%M:%S') if row[6] else ''}
                for row in cursor.fetchall()
            ]
            cursor.close()
            conn.close()
            return jsonify({'users': users})
        elif request.method == 'POST':
            data = request.get_json()
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            role = data.get('role', 'user')
            if not username or not email or not password:
                return jsonify({'error': 'All fields are required'}), 400
            # Check if user exists
            cursor.execute('SELECT id FROM users WHERE username=%s OR email=%s', (username, email))
            if cursor.fetchone():
                return jsonify({'error': 'Username or email already exists'}), 400
            import bcrypt
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute('INSERT INTO users (username, email, password_hash, first_name, last_name, role) VALUES (%s, %s, %s, %s, %s, %s)', (username, email, password_hash, first_name, last_name, role))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True})
        elif request.method == 'DELETE':
            data = request.get_json()
            user_id = data.get('id')
            if not user_id:
                return jsonify({'error': 'User ID required'}), 400
            # Prevent admin from deleting self
            cursor.execute('SELECT username FROM users WHERE id=%s', (user_id,))
            row = cursor.fetchone()
            if not row or row[0] == 'admin':
                return jsonify({'error': 'Cannot delete this user'}), 400
            cursor.execute('DELETE FROM users WHERE id=%s', (user_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Admin user management error: {e}")
        if conn:
            conn.rollback()
        return jsonify({'error': 'Failed to manage users'}), 500

@app.route('/api/admin/reset_password', methods=['POST'])
def api_admin_reset_password():
    if 'user_id' not in session or session.get('username') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    user_id = data.get('id')
    new_password = data.get('new_password')
    if not user_id or not new_password:
        return jsonify({'error': 'User ID and new password required'}), 400
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    try:
        cursor = conn.cursor()
        # Prevent admin from resetting their own password here (optional)
        cursor.execute('SELECT username FROM users WHERE id=%s', (user_id,))
        row = cursor.fetchone()
        if not row or row[0] == 'admin':
            return jsonify({'error': 'Cannot reset password for this user'}), 400
        import bcrypt
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute('UPDATE users SET password_hash=%s WHERE id=%s', (password_hash, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Admin reset password error: {e}")
        if conn:
            conn.rollback()
        return jsonify({'error': 'Failed to reset password'}), 500

if __name__ == '__main__':
    # Create tables when the app starts
    create_tables()
    print("\n" + "="*50)
    print("CHURN PREDICTION SYSTEM")
    print("="*50)
    print("Default login credentials:")
    print("Username: admin")
    print("Password: admin123")
    print("OR")
    print("Username: demo")
    print("Password: demo123")
    print("="*50)
    app.run(debug=True, host='0.0.0.0', port=5000) 