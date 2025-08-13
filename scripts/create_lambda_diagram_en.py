#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HADS Lambda internal architecture diagram generation script (English version)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import matplotlib.colors as mcolors
import os

# Font settings
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10

# Figure size and settings
fig, ax = plt.subplots(1, 1, figsize=(16, 12))
ax.set_xlim(0, 16)
ax.set_ylim(0, 12)
ax.axis('off')

# Color palette
colors = {
    'lambda': '#FF9500',      # AWS Lambda orange
    'handler': '#4CAF50',     # Green
    'hads_core': '#2196F3',   # Blue
    'auth': '#9C27B0',        # Purple
    'routing': '#FF5722',     # Red
    'views': '#607D8B',       # Grey
    'templates': '#00BCD4',   # Cyan
    'debug': '#795548',       # Brown
    'arrow': '#666666'        # Arrow
}

def create_rounded_box(ax, x, y, width, height, label, color, text_color='white', fontsize=10):
    """Create rounded box"""
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
    """Create arrow"""
    arrow = ConnectionPatch(start, end, "data", "data",
                          arrowstyle=style, shrinkA=5, shrinkB=5,
                          mutation_scale=20, fc=color, ec=color, lw=width)
    ax.add_patch(arrow)
    return arrow

# Title
ax.text(8, 11.5, 'HADS Lambda Function Internal Architecture', 
        ha='center', va='center', fontsize=16, weight='bold')

# API Gateway (input)
create_rounded_box(ax, 0.5, 9.5, 2, 1, 'API Gateway\nEvent', colors['lambda'])

# Lambda Handler Entry Point
create_rounded_box(ax, 4, 9.5, 2.5, 1, 'lambda_handler()\nEntry Point', colors['handler'])

# HADS Framework Core Components
# Master Class
create_rounded_box(ax, 0.5, 7.5, 2.5, 1.2, 'Master Class\n- Initialize settings\n- Setup request/context', colors['hads_core'])

# Authentication System
create_rounded_box(ax, 3.5, 7.5, 2.5, 1.2, 'Authentication\n- Cognito integration\n- Cookie handling\n- NO_AUTH mode', colors['auth'])

# Router System
create_rounded_box(ax, 6.5, 7.5, 2.5, 1.2, 'URL Router\n- urls.py patterns\n- View resolution\n- Path parameters', colors['routing'])

# Request Processing Layer
create_rounded_box(ax, 0.5, 5.5, 3, 1.5, 'Request Processing\n- Form data parsing\n- MultiDict support\n- Header processing\n- Body parsing', colors['hads_core'])

# Business Logic Layer
create_rounded_box(ax, 4, 5.5, 3, 1.5, 'Business Logic\n- View functions\n- Database access\n- External API calls\n- Business rules', colors['views'])

# Template Engine
create_rounded_box(ax, 7.5, 5.5, 3, 1.5, 'Template Engine\n- Jinja2 rendering\n- Context variables\n- Template inheritance\n- Static file handling', colors['templates'])

# Response Generation
create_rounded_box(ax, 2, 3.5, 3, 1.2, 'Response Generation\n- HTTP status codes\n- Headers & cookies\n- Content-Type handling', colors['hads_core'])

# Debug System (new feature)
create_rounded_box(ax, 6, 3.5, 3, 1.2, 'Debug System\n- Direct execution\n- Command line args\n- Event simulation', colors['debug'])

# Mock Environment (development)
create_rounded_box(ax, 0.5, 1.5, 4, 1.2, 'Mock Environment (Development)\n- DynamoDB mock\n- SSM mock\n- Cognito mock\n- Local testing', colors['debug'])

# Output
create_rounded_box(ax, 6, 1.5, 2.5, 1.2, 'HTTP Response\n- JSON/HTML\n- Status codes\n- Headers', colors['lambda'])

# Development Tools
create_rounded_box(ax, 10, 7.5, 3.5, 1.2, 'Development Tools\n- Proxy server\n- Static file server\n- SAM Local integration', colors['debug'])

create_rounded_box(ax, 11, 5.5, 3, 1.5, 'Local Development\n- hads-admin.py proxy\n- Direct lambda execution\n- Cookie debugging\n- Request simulation', colors['debug'])

# External Services
create_rounded_box(ax, 11, 3.5, 3, 1.2, 'AWS Services\n- DynamoDB\n- S3\n- Cognito\n- SSM Parameter Store', colors['lambda'])

create_rounded_box(ax, 9, 1.5, 2.5, 1.2, 'Static Files\n- CSS/JS\n- Images\n- Assets', colors['templates'])

# Arrows showing flow
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

# Legend
legend_y = 0.5
legend_items = [
    ('Core Framework', colors['hads_core']),
    ('Authentication', colors['auth']),
    ('Routing', colors['routing']),
    ('Business Logic', colors['views']),
    ('Templates', colors['templates']),
    ('Development Tools', colors['debug']),
    ('AWS Services', colors['lambda'])
]

for i, (label, color) in enumerate(legend_items):
    x = i * 2.2 + 0.5
    create_rounded_box(ax, x, legend_y, 0.3, 0.2, '', color)
    ax.text(x + 0.4, legend_y + 0.1, label, ha='left', va='center', fontsize=8)

plt.tight_layout()

# Save image
output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'images', 'lambda_en.png')
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.close()

print(f"Lambda architecture diagram (English) has been created: {output_path}")