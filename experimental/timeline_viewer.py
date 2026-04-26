import json
import argparse
from datetime import datetime
from collections import defaultdict
import os

def parse_timeline_json(file_path):
    """Google MapのタイムラインJSONを解析"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    timeline_data = defaultdict(list)
    
    for edit in data.get('timelineEdits', []):
        # rawSignalのタイムスタンプを抽出
        if 'rawSignal' in edit:
            signal = edit['rawSignal'].get('signal', {})
            
            # アクティビティレコード
            if 'activityRecord' in signal:
                activity = signal['activityRecord']
                timestamp = activity.get('timestamp')
                if timestamp:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    date_key = dt.strftime('%Y-%m-%d')
                    
                    timeline_data[date_key].append({
                        'time': dt.strftime('%H:%M:%S'),
                        'timestamp': timestamp,
                        'type': 'activity',
                        'activities': activity.get('detectedActivities', []),
                        'datetime': dt
                    })
            
            # 位置情報レコード
            if 'locationRecord' in signal:
                location = signal['locationRecord']
                timestamp = location.get('timestamp')
                if timestamp:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    date_key = dt.strftime('%Y-%m-%d')
                    
                    point = location.get('point', {})
                    lat = point.get('latE7', 0) / 1e7 if 'latE7' in point else None
                    lng = point.get('lngE7', 0) / 1e7 if 'lngE7' in point else None
                    
                    timeline_data[date_key].append({
                        'time': dt.strftime('%H:%M:%S'),
                        'timestamp': timestamp,
                        'type': 'location',
                        'lat': lat,
                        'lng': lng,
                        'accuracy': location.get('accuracy'),
                        'datetime': dt
                    })
        
        # placeAggregatesの処理
        if 'placeAggregates' in edit:
            place_agg = edit['placeAggregates']
            process_window = place_agg.get('processWindow', {})
            
            start_time = process_window.get('startTime')
            end_time = process_window.get('endTime')
            
            if start_time:
                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                date_key = dt.strftime('%Y-%m-%d')
                
                timeline_data[date_key].append({
                    'time': dt.strftime('%H:%M:%S'),
                    'timestamp': start_time,
                    'type': 'place_aggregate',
                    'start_time': start_time,
                    'end_time': end_time,
                    'places': place_agg.get('placeAggregateInfo', []),
                    'datetime': dt
                })
    
    # 各日のデータを時間順にソート
    for date_key in timeline_data:
        timeline_data[date_key].sort(key=lambda x: x['datetime'])
    
    return dict(timeline_data)

def generate_text_report(timeline_data, output_file):
    """テキストレポートを生成"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("Google Maps Timeline Report\n")
        f.write("=" * 80 + "\n\n")
        
        for date in sorted(timeline_data.keys(), reverse=True):
            f.write(f"\n{'=' * 80}\n")
            f.write(f"日付: {date}\n")
            f.write(f"{'=' * 80}\n")
            f.write(f"記録数: {len(timeline_data[date])} 件\n\n")
            
            for entry in timeline_data[date]:
                f.write(f"  時刻: {entry['time']} ({entry['timestamp']})\n")
                f.write(f"  種類: {entry['type']}\n")
                
                if entry['type'] == 'activity':
                    f.write("  検出されたアクティビティ:\n")
                    for act in entry['activities']:
                        activity_type = act.get('activityType', 'UNKNOWN')
                        probability = act.get('probability', 0)
                        f.write(f"    - {activity_type}: {probability:.2%}\n")
                
                elif entry['type'] == 'location':
                    if entry['lat'] and entry['lng']:
                        f.write(f"  位置: ({entry['lat']:.6f}, {entry['lng']:.6f})\n")
                        f.write(f"  精度: {entry['accuracy']}m\n")
                        f.write(f"  Google Maps: https://www.google.com/maps?q={entry['lat']},{entry['lng']}\n")
                
                elif entry['type'] == 'place_aggregate':
                    f.write(f"  期間: {entry['start_time']} ~ {entry['end_time']}\n")
                    f.write(f"  訪問場所数: {len(entry['places'])}\n")
                    for place in entry['places'][:3]:  # 上位3件のみ表示
                        score = place.get('score', 0)
                        place_id = place.get('placeId', 'N/A')
                        point = place.get('placePoint', {})
                        lat = point.get('latE7', 0) / 1e7 if 'latE7' in point else None
                        lng = point.get('lngE7', 0) / 1e7 if 'lngE7' in point else None
                        f.write(f"    - スコア: {score}, Place ID: {place_id}\n")
                        if lat and lng:
                            f.write(f"      位置: ({lat:.6f}, {lng:.6f})\n")
                
                f.write("  " + "-" * 76 + "\n\n")
            
            f.write("\n")

def generate_html_report(timeline_data, output_file):
    """インタラクティブなHTMLレポートを生成"""
    html_content = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google Maps Timeline Viewer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }
        
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .stats {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
        }
        
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        
        .content {
            padding: 30px;
        }
        
        .date-selector {
            margin-bottom: 30px;
            text-align: center;
        }
        
        select {
            padding: 12px 24px;
            font-size: 16px;
            border: 2px solid #667eea;
            border-radius: 10px;
            background: white;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        select:hover {
            background: #f0f0f0;
        }
        
        .timeline {
            position: relative;
            padding-left: 50px;
        }
        
        .timeline::before {
            content: '';
            position: absolute;
            left: 20px;
            top: 0;
            bottom: 0;
            width: 4px;
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
            border-radius: 2px;
        }
        
        .timeline-item {
            position: relative;
            margin-bottom: 30px;
            background: #f8f9fa;
            border-radius: 15px;
            padding: 20px;
            transition: all 0.3s;
            cursor: pointer;
        }
        
        .timeline-item:hover {
            transform: translateX(5px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }
        
        .timeline-item::before {
            content: '';
            position: absolute;
            left: -38px;
            top: 20px;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: white;
            border: 4px solid #667eea;
            z-index: 1;
        }
        
        .timeline-item.activity::before {
            border-color: #28a745;
        }
        
        .timeline-item.location::before {
            border-color: #dc3545;
        }
        
        .timeline-item.place_aggregate::before {
            border-color: #ffc107;
        }
        
        .time-badge {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .type-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.85em;
            margin-left: 10px;
            font-weight: bold;
        }
        
        .type-badge.activity {
            background: #d4edda;
            color: #155724;
        }
        
        .type-badge.location {
            background: #f8d7da;
            color: #721c24;
        }
        
        .type-badge.place_aggregate {
            background: #fff3cd;
            color: #856404;
        }
        
        .details {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 2px solid #e0e0e0;
        }
        
        .activity-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 10px;
            margin-top: 10px;
        }
        
        .activity-item {
            background: white;
            padding: 10px;
            border-radius: 8px;
            border-left: 4px solid #28a745;
        }
        
        .activity-name {
            font-weight: bold;
            color: #333;
        }
        
        .activity-prob {
            color: #666;
            font-size: 0.9em;
        }
        
        .progress-bar {
            height: 6px;
            background: #e0e0e0;
            border-radius: 3px;
            margin-top: 5px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 3px;
            transition: width 0.3s;
        }
        
        .location-info {
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-top: 10px;
        }
        
        .map-link {
            display: inline-block;
            margin-top: 10px;
            padding: 8px 16px;
            background: #dc3545;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            transition: all 0.3s;
        }
        
        .map-link:hover {
            background: #c82333;
            transform: translateY(-2px);
        }
        
        .place-list {
            margin-top: 10px;
        }
        
        .place-item {
            background: white;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 8px;
            border-left: 4px solid #ffc107;
        }
        
        .no-data {
            text-align: center;
            padding: 50px;
            color: #999;
            font-size: 1.2em;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📍 Google Maps Timeline</h1>
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-value" id="total-days">0</div>
                    <div class="stat-label">日数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="total-records">0</div>
                    <div class="stat-label">総記録数</div>
                </div>
            </div>
        </header>
        
        <div class="content">
            <div class="date-selector">
                <label for="date-select" style="font-size: 1.2em; margin-right: 10px;">📅 日付を選択:</label>
                <select id="date-select">
                    <option value="">日付を選択してください</option>
                </select>
            </div>
            
            <div class="timeline" id="timeline">
                <div class="no-data">日付を選択してタイムラインを表示してください</div>
            </div>
        </div>
    </div>
    
    <script>
        const timelineData = """ + json.dumps(timeline_data, ensure_ascii=False, indent=2) + """;
        
        // 統計情報を更新
        document.getElementById('total-days').textContent = Object.keys(timelineData).length;
        let totalRecords = 0;
        for (let date in timelineData) {
            totalRecords += timelineData[date].length;
        }
        document.getElementById('total-records').textContent = totalRecords;
        
        // 日付セレクタを設定
        const dateSelect = document.getElementById('date-select');
        const dates = Object.keys(timelineData).sort().reverse();
        
        dates.forEach(date => {
            const option = document.createElement('option');
            option.value = date;
            option.textContent = `${date} (${timelineData[date].length}件)`;
            dateSelect.appendChild(option);
        });
        
        // 日付選択時の処理
        dateSelect.addEventListener('change', function() {
            const selectedDate = this.value;
            if (!selectedDate) {
                document.getElementById('timeline').innerHTML = '<div class="no-data">日付を選択してタイムラインを表示してください</div>';
                return;
            }
            
            displayTimeline(selectedDate);
        });
        
        function displayTimeline(date) {
            const timeline = document.getElementById('timeline');
            const entries = timelineData[date];
            
            if (!entries || entries.length === 0) {
                timeline.innerHTML = '<div class="no-data">この日のデータはありません</div>';
                return;
            }
            
            let html = '';
            
            entries.forEach(entry => {
                html += `<div class="timeline-item ${entry.type}">`;
                html += `<span class="time-badge">${entry.time}</span>`;
                html += `<span class="type-badge ${entry.type}">${getTypeName(entry.type)}</span>`;
                html += `<div class="details">`;
                
                if (entry.type === 'activity') {
                    html += '<div class="activity-list">';
                    entry.activities.forEach(act => {
                        const prob = (act.probability * 100).toFixed(0);
                        html += `<div class="activity-item">`;
                        html += `<div class="activity-name">${getActivityName(act.activityType)}</div>`;
                        html += `<div class="activity-prob">${prob}%</div>`;
                        html += `<div class="progress-bar"><div class="progress-fill" style="width: ${prob}%"></div></div>`;
                        html += `</div>`;
                    });
                    html += '</div>';
                }
                else if (entry.type === 'location' && entry.lat && entry.lng) {
                    html += '<div class="location-info">';
                    html += `<strong>📍 位置情報:</strong><br>`;
                    html += `緯度: ${entry.lat.toFixed(6)}, 経度: ${entry.lng.toFixed(6)}<br>`;
                    if (entry.accuracy) {
                        html += `精度: ${entry.accuracy}m<br>`;
                    }
                    html += `<a href="https://www.google.com/maps?q=${entry.lat},${entry.lng}" target="_blank" class="map-link">🗺️ Google Mapsで開く</a>`;
                    html += '</div>';
                }
                else if (entry.type === 'place_aggregate') {
                    html += `<strong>期間:</strong> ${entry.start_time} ~ ${entry.end_time}<br>`;
                    html += `<strong>訪問場所数:</strong> ${entry.places.length}<br>`;
                    if (entry.places.length > 0) {
                        html += '<div class="place-list">';
                        entry.places.slice(0, 5).forEach(place => {
                            html += '<div class="place-item">';
                            html += `<strong>スコア:</strong> ${place.score}<br>`;
                            if (place.placePoint && place.placePoint.latE7 && place.placePoint.lngE7) {
                                const lat = place.placePoint.latE7 / 1e7;
                                const lng = place.placePoint.lngE7 / 1e7;
                                html += `Place ID: ${place.placeId}<br>`;
                                html += `<a href="https://www.google.com/maps?q=${lat},${lng}" target="_blank" class="map-link">🗺️ 地図で見る</a>`;
                            }
                            html += '</div>';
                        });
                        html += '</div>';
                    }
                }
                
                html += '</div></div>';
            });
            
            timeline.innerHTML = html;
        }
        
        function getTypeName(type) {
            const names = {
                'activity': '🏃 アクティビティ',
                'location': '📍 位置情報',
                'place_aggregate': '📊 場所集計'
            };
            return names[type] || type;
        }
        
        function getActivityName(type) {
            const names = {
                'STILL': '静止',
                'ON_FOOT': '徒歩',
                'WALKING': '歩行',
                'RUNNING': 'ランニング',
                'IN_VEHICLE': '車両',
                'IN_RAIL_VEHICLE': '鉄道',
                'IN_ROAD_VEHICLE': '道路車両',
                'ON_BICYCLE': '自転車',
                'UNKNOWN': '不明'
            };
            return names[type] || type;
        }
    </script>
</body>
</html>"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    parser = argparse.ArgumentParser(description="Generate timeline reports from Google Timeline Edits JSON.")
    parser.add_argument(
        "--input-json",
        default="Timeline Edits.json",
        help="Path to Google Timeline Edits JSON file",
    )
    parser.add_argument(
        "--output-dir",
        default="timeline_output",
        help="Directory to write text/html reports",
    )
    args = parser.parse_args()

    json_file = args.input_json
    output_dir = args.output_dir

    if not os.path.exists(json_file):
        raise FileNotFoundError(f"Input JSON not found: {json_file}")
    
    # 出力ディレクトリを作成
    os.makedirs(output_dir, exist_ok=True)
    
    print("📖 タイムラインJSONを読み込み中...")
    timeline_data = parse_timeline_json(json_file)
    
    print(f"✅ {len(timeline_data)} 日分のデータを解析しました")
    
    # テキストレポート生成
    text_output = os.path.join(output_dir, "timeline_report.txt")
    print(f"\n📝 テキストレポートを生成中: {text_output}")
    generate_text_report(timeline_data, text_output)
    print(f"✅ テキストレポート完成")
    
    # HTMLレポート生成
    html_output = os.path.join(output_dir, "timeline_viewer.html")
    print(f"\n🌐 HTMLレポートを生成中: {html_output}")
    generate_html_report(timeline_data, html_output)
    print(f"✅ HTMLレポート完成")
    
    # サマリー表示
    print("\n" + "=" * 60)
    print("📊 タイムラインサマリー")
    print("=" * 60)
    total_records = sum(len(records) for records in timeline_data.values())
    print(f"期間: {min(timeline_data.keys())} ~ {max(timeline_data.keys())}")
    print(f"総日数: {len(timeline_data)} 日")
    print(f"総記録数: {total_records} 件")
    print("\n各日の記録数:")
    for date in sorted(timeline_data.keys(), reverse=True)[:10]:
        print(f"  {date}: {len(timeline_data[date])} 件")
    
    print("\n" + "=" * 60)
    print(f"✨ 完了！HTMLファイルをブラウザで開いてください:")
    print(f"   {html_output}")
    print("=" * 60)

if __name__ == "__main__":
    main()
