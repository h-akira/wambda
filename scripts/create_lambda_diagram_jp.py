#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WAMBDA Lambda内部構造図を生成するスクリプト（日本語版）
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import matplotlib.colors as mcolors
import os

# 日本語フォントの設定
plt.rcParams['font.family'] = ['DejaVu Sans', 'Hiragino Sans', 'Yu Gothic', 'Meiryo', 'Takao', 'IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP']
plt.rcParams['font.size'] = 10

# 図のサイズと設定
fig, ax = plt.subplots(1, 1, figsize=(16, 12))
ax.set_xlim(0, 16)
ax.set_ylim(0, 12)
ax.axis('off')

# カラーパレット
colors = {
    'lambda': '#FF9500',      # AWS Lambda オレンジ
    'handler': '#4CAF50',     # 緑
    'hads_core': '#2196F3',   # 青
    'auth': '#9C27B0',        # 紫
    'routing': '#FF5722',     # 赤
    'views': '#607D8B',       # グレー
    'templates': '#00BCD4',   # シアン
    'debug': '#795548',       # 茶色
    'arrow': '#666666'        # 矢印
}

def create_rounded_box(ax, x, y, width, height, label, color, text_color='white', fontsize=10):
    """角丸の箱を作成"""
    box = FancyBboxPatch(
        (x, y), width, height,
        boxstyle="round,pad=0.05",
        facecolor=color,
        edgecolor='black',
        linewidth=1
    )
    ax.add_patch(box)
    ax.text(x + width/2, y + height/2, label, 
            ha='center', va='center', color=text_color, 
            fontsize=fontsize, weight='bold')
    return box

def create_arrow(ax, start, end, color='#666666', style='->', width=1.5):
    """矢印を作成"""
    arrow = ConnectionPatch(start, end, "data", "data",
                          arrowstyle=style, shrinkA=5, shrinkB=5,
                          mutation_scale=20, fc=color, ec=color, lw=width)
    ax.add_patch(arrow)
    return arrow

# タイトル
ax.text(8, 11.5, 'WAMBDA Lambda関数 内部アーキテクチャ', 
        ha='center', va='center', fontsize=16, weight='bold')

# API Gateway (入力)
create_rounded_box(ax, 0.5, 9.5, 2, 1, 'API Gateway\nイベント', colors['lambda'])

# Lambda Handler Entry Point
create_rounded_box(ax, 4, 9.5, 2.5, 1, 'lambda_handler()\nエントリーポイント', colors['handler'])

# WAMBDA Framework Core Components
# Master Class
create_rounded_box(ax, 0.5, 7.5, 2.5, 1.2, 'Masterクラス\n- 設定初期化\n- リクエスト/コンテキスト設定', colors['hads_core'])

# Authentication System
create_rounded_box(ax, 3.5, 7.5, 2.5, 1.2, '認証システム\n- Cognito統合\n- クッキー処理\n- NO_AUTHモード', colors['auth'])

# Router System
create_rounded_box(ax, 6.5, 7.5, 2.5, 1.2, 'URLルーター\n- urls.pyパターン\n- ビュー解決\n- パスパラメータ', colors['routing'])

# Request Processing Layer
create_rounded_box(ax, 0.5, 5.5, 3, 1.5, 'リクエスト処理\n- フォームデータ解析\n- MultiDict対応\n- ヘッダー処理\n- ボディ解析', colors['hads_core'])

# Business Logic Layer
create_rounded_box(ax, 4, 5.5, 3, 1.5, 'ビジネスロジック\n- ビュー関数\n- データベースアクセス\n- 外部API呼び出し\n- ビジネスルール', colors['views'])

# Template Engine
create_rounded_box(ax, 7.5, 5.5, 3, 1.5, 'テンプレートエンジン\n- Jinja2レンダリング\n- コンテキスト変数\n- テンプレート継承\n- 静的ファイル処理', colors['templates'])

# Response Generation
create_rounded_box(ax, 2, 3.5, 3, 1.2, 'レスポンス生成\n- HTTPステータスコード\n- ヘッダー & クッキー\n- Content-Type処理', colors['hads_core'])

# Debug System (新機能)
create_rounded_box(ax, 6, 3.5, 3, 1.2, 'デバッグシステム\n- 直接実行\n- コマンドライン引数\n- イベントシミュレーション', colors['debug'])

# Mock Environment (開発用)
create_rounded_box(ax, 0.5, 1.5, 4, 1.2, 'モック環境（開発用）\n- DynamoDBモック\n- SSMモック\n- Cognitoモック\n- ローカルテスト', colors['debug'])

# Output
create_rounded_box(ax, 6, 1.5, 2.5, 1.2, 'HTTPレスポンス\n- JSON/HTML\n- ステータスコード\n- ヘッダー', colors['lambda'])

# Development Tools
create_rounded_box(ax, 10, 7.5, 3.5, 1.2, '開発ツール\n- プロキシサーバー\n- 静的ファイルサーバー\n- SAM Local統合', colors['debug'])

create_rounded_box(ax, 11, 5.5, 3, 1.5, 'ローカル開発\n- hads-admin.pyプロキシ\n- Lambda直接実行\n- クッキーデバッグ\n- リクエストシミュレーション', colors['debug'])

# External Services
create_rounded_box(ax, 11, 3.5, 3, 1.2, 'AWSサービス\n- DynamoDB\n- S3\n- Cognito\n- SSMパラメータストア', colors['lambda'])

create_rounded_box(ax, 9, 1.5, 2.5, 1.2, '静的ファイル\n- CSS/JS\n- 画像\n- アセット', colors['templates'])

# 矢印で流れを示す
# Main flow
create_arrow(ax, (2.5, 10), (4, 10))  # API Gateway -> lambda_handler
create_arrow(ax, (5.25, 9.5), (5.25, 8.7))  # lambda_handler -> processing

# Horizontal flow in processing layer
create_arrow(ax, (3, 8.1), (3.5, 8.1))  # Master -> Auth
create_arrow(ax, (6, 8.1), (6.5, 8.1))  # Auth -> Router

# Down to business logic
create_arrow(ax, (1.75, 7.5), (1.75, 7))  # Master -> Request Processing
create_arrow(ax, (4.75, 7.5), (5.5, 7))  # Auth -> Business Logic
create_arrow(ax, (7.75, 7.5), (9, 7))    # Router -> Templates

# To response
create_arrow(ax, (2, 5.5), (2.5, 4.7))   # Request -> Response
create_arrow(ax, (5.5, 5.5), (3.5, 4.7)) # Business -> Response
create_arrow(ax, (9, 5.5), (4.5, 4.7))   # Templates -> Response

# Debug connections
create_arrow(ax, (7.5, 4.1), (7.5, 3.5))  # Debug system
create_arrow(ax, (5, 3.5), (6, 2.7))      # Response -> Output

# Development tools connections
create_arrow(ax, (11.75, 7.5), (11.75, 7), color=colors['debug'], style='<->')  # Bidirectional
create_arrow(ax, (12.5, 5.5), (12.5, 4.7), color=colors['debug'])

# Mock environment
create_arrow(ax, (2.5, 2.7), (2.5, 3.5), color=colors['debug'], style='<->')

# 凡例
legend_y = 0.5
legend_items = [
    ('コアフレームワーク', colors['hads_core']),
    ('認証', colors['auth']),
    ('ルーティング', colors['routing']),
    ('ビジネスロジック', colors['views']),
    ('テンプレート', colors['templates']),
    ('開発ツール', colors['debug']),
    ('AWSサービス', colors['lambda'])
]

for i, (label, color) in enumerate(legend_items):
    x = i * 2.2 + 0.5
    create_rounded_box(ax, x, legend_y, 0.3, 0.2, '', color)
    ax.text(x + 0.4, legend_y + 0.1, label, ha='left', va='center', fontsize=8)

plt.tight_layout()

# 画像を保存
output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'images', 'lambda_jp.png')
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.close()

print(f"Lambda architecture diagram (Japanese) has been created: {output_path}")