# 静的ファイル管理

HADSでは、CSS、JavaScript、画像などの静的ファイルをS3から効率的に配信する仕組みを提供しています。このページでは、静的ファイルの管理方法を詳しく説明します。

## 📁 静的ファイルの構造

### 基本ディレクトリ構造

```
static/
├── css/
│   ├── bootstrap.min.css
│   ├── app.css
│   └── components/
│       ├── navbar.css
│       └── footer.css
├── js/
│   ├── app.js
│   ├── form-validation.js
│   └── lib/
│       ├── bootstrap.bundle.min.js
│       └── jquery.min.js
├── images/
│   ├── logo.png
│   ├── favicon.ico
│   ├── heroes/
│   │   └── hero-bg.jpg
│   └── icons/
│       ├── user.svg
│       └── settings.svg
├── fonts/
│   ├── custom-font.woff2
│   └── icons.woff
└── docs/
    ├── manual.pdf
    └── terms.pdf
```

## ⚙️ 設定と管理

### CLIによる設定

静的ファイルの設定はすべてコマンドラインオプションで制御します：

```bash
# 静的ファイルサーバーの設定
hads-admin.py static --static-dir static --static-url /static -p 8080

# プロキシサーバーでの静的ファイル統合
hads-admin.py proxy --static-dir static --static-url /static
```

| 設定項目 | 説明 |
|----------|------|
| `static.local` | ローカル開発時の静的ファイルディレクトリ |
| `static.s3` | 本番環境のS3バケットパス |
| `local_server.port.static` | ローカル静的ファイルサーバーのポート |

### settings.py 設定

```python
# Lambda/project/settings.py
import os

# 静的ファイル設定
STATIC_URL = "/static"  # URLプレフィックス

# 開発環境でのローカルパス
STATIC_ROOT = os.path.join(BASE_DIR, "../static")

# 本番環境での静的ファイル配信設定
if not DEBUG:
    # CloudFrontやS3の設定
    STATIC_URL = "https://cdn.example.com/static/"
```

## 🚀 ローカル開発での静的ファイル

### 静的ファイルサーバーの起動

```bash
# 静的ファイルサーバーを起動
sam build && sam deploy static

# プロキシサーバーを起動（推奨）
hads-admin.py proxy
```

### ローカル開発の仕組み

ローカル開発時は3つのサーバーが連携します：

1. **SAM Local** (ポート3000) - Lambda関数
2. **静的ファイルサーバー** (ポート8080) - 静的ファイル配信
3. **プロキシサーバー** (ポート8000) - 統合エンドポイント

```
ブラウザ (localhost:8000)
    ↓
プロキシサーバー
    ├── /static/* → 静的ファイルサーバー (8080)
    └── その他 → SAM Local (3000)
```

## 🌐 テンプレートでの静的ファイル使用

### static() 関数の使用

```html
<!DOCTYPE html>
<html>
<head>
    <!-- CSS -->
    <link href="{{ static(master, 'css/bootstrap.min.css') }}" rel="stylesheet">
    <link href="{{ static(master, 'css/app.css') }}" rel="stylesheet">
    
    <!-- ファビコン -->
    <link rel="icon" href="{{ static(master, 'favicon.ico') }}" type="image/x-icon">
    
    <!-- プリロード -->
    <link rel="preload" href="{{ static(master, 'fonts/custom-font.woff2') }}" 
          as="font" type="font/woff2" crossorigin>
</head>
<body>
    <!-- 画像 -->
    <img src="{{ static(master, 'images/logo.png') }}" alt="ロゴ">
    
    <!-- 背景画像をCSSで使用 -->
    <div class="hero" style="background-image: url('{{ static(master, 'images/heroes/hero-bg.jpg') }}');">
        <h1>ようこそ</h1>
    </div>
    
    <!-- JavaScript -->
    <script src="{{ static(master, 'js/lib/jquery.min.js') }}"></script>
    <script src="{{ static(master, 'js/app.js') }}"></script>
</body>
</html>
```

### CSSでの静的ファイル参照

```css
/* static/css/app.css */

/* フォントの読み込み */
@font-face {
    font-family: 'CustomFont';
    src: url('../fonts/custom-font.woff2') format('woff2'),
         url('../fonts/custom-font.woff') format('woff');
    font-display: swap;
}

/* 背景画像 */
.hero {
    background-image: url('../images/heroes/hero-bg.jpg');
    background-size: cover;
    background-position: center;
}

/* アイコン */
.icon-user {
    background-image: url('../images/icons/user.svg');
    width: 24px;
    height: 24px;
    background-repeat: no-repeat;
}

/* レスポンシブ画像 */
.logo {
    content: url('../images/logo.png');
    max-width: 100%;
    height: auto;
}

@media (max-width: 768px) {
    .logo {
        content: url('../images/logo-small.png');
    }
}
```

## ☁️ S3での静的ファイル配信

### S3バケットの設定

```bash
# S3バケットを作成
aws s3 mb s3://your-static-files-bucket --region ap-northeast-1

# パブリック読み取りアクセスを設定
aws s3api put-bucket-policy --bucket your-static-files-bucket --policy '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::your-static-files-bucket/*"
    }
  ]
}'
```

### 静的ファイルの同期

```bash
# 静的ファイルをS3にアップロード
sam build && sam deploy2s3

# 手動でのアップロード
aws s3 sync static/ s3://your-static-files-bucket/static/ --delete

# 特定ファイルタイプのキャッシュ設定
aws s3 sync static/ s3://your-static-files-bucket/static/ \
  --exclude "*" \
  --include "*.css" \
  --include "*.js" \
  --cache-control "max-age=31536000"  # 1年間キャッシュ
```

### CloudFront CDN の設定

```yaml
# template.yaml でCloudFrontを追加
Resources:
  StaticFilesCDN:
    Type: AWS::CloudFront::Distribution
    Properties:
      DistributionConfig:
        Origins:
          - Id: S3Origin
            DomainName: !GetAtt StaticFilesBucket.DomainName
            S3OriginConfig:
              OriginAccessIdentity: !Sub "origin-access-identity/cloudfront/${OriginAccessIdentity}"
        DefaultCacheBehavior:
          TargetOriginId: S3Origin
          ViewerProtocolPolicy: redirect-to-https
          CachePolicyId: 4135ea2d-6df8-44a3-9df3-4b5a84be39ad  # Managed-CachingOptimized
        PriceClass: PriceClass_100
        Enabled: true
        
  StaticFilesBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub "${AWS::StackName}-static-files"
```

## 🎨 アセット最適化

### CSS の最適化

```css
/* static/css/app.css */

/* 重要なスタイル（Above the fold） */
.header, .hero {
    /* クリティカルCSS */
}

/* 遅延読み込みCSS */
/* static/css/non-critical.css */
.footer, .sidebar {
    /* 非重要CSS */
}
```

```html
<!-- テンプレートでの最適化 -->
<head>
    <!-- クリティカルCSSは直接インライン -->
    <style>
        /* クリティカルCSSの内容 */
    </style>
    
    <!-- 非クリティカルCSSは遅延読み込み -->
    <link rel="preload" href="{{ static(master, 'css/non-critical.css') }}" 
          as="style" onload="this.onload=null;this.rel='stylesheet'">
    <noscript>
        <link rel="stylesheet" href="{{ static(master, 'css/non-critical.css') }}">
    </noscript>
</head>
```

### JavaScript の最適化

```javascript
// static/js/app.js

// 重要な機能（即座に実行）
(function() {
    'use strict';
    
    // ナビゲーション制御
    function initNavigation() {
        // ...
    }
    
    // フォーム検証
    function initFormValidation() {
        // ...
    }
    
    // DOM読み込み完了後に実行
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initNavigation();
            initFormValidation();
        });
    } else {
        initNavigation();
        initFormValidation();
    }
})();

// 非重要な機能（遅延読み込み）
function loadNonCriticalFeatures() {
    // アナリティクス
    // チャット機能
    // その他の非重要機能
}

// ページ読み込み完了後に非重要機能を読み込み
window.addEventListener('load', loadNonCriticalFeatures);
```

### 画像の最適化

```html
<!-- レスポンシブ画像 -->
<picture>
    <source media="(max-width: 768px)" 
            srcset="{{ static(master, 'images/hero-mobile.webp') }}" type="image/webp">
    <source media="(max-width: 768px)" 
            srcset="{{ static(master, 'images/hero-mobile.jpg') }}" type="image/jpeg">
    <source srcset="{{ static(master, 'images/hero-desktop.webp') }}" type="image/webp">
    <img src="{{ static(master, 'images/hero-desktop.jpg') }}" 
         alt="ヒーロー画像" 
         loading="lazy"
         width="1200" 
         height="600">
</picture>

<!-- 遅延読み込み -->
<img src="{{ static(master, 'images/placeholder.svg') }}" 
     data-src="{{ static(master, 'images/actual-image.jpg') }}" 
     alt="画像"
     loading="lazy"
     class="lazy-load">
```

## 🔧 開発ツールとの連携

### ビルドプロセス

```json
// package.json (静的ファイルのビルド用)
{
  "scripts": {
    "build-css": "sass static/scss:static/css --style compressed",
    "build-js": "webpack --mode production",
    "watch-css": "sass static/scss:static/css --watch",
    "watch-js": "webpack --mode development --watch",
    "build": "npm run build-css && npm run build-js",
    "dev": "npm run watch-css & npm run watch-js"
  },
  "devDependencies": {
    "sass": "^1.50.0",
    "webpack": "^5.70.0",
    "webpack-cli": "^4.9.0"
  }
}
```

### Webpack設定例

```javascript
// webpack.config.js
const path = require('path');

module.exports = {
  entry: {
    app: './static/src/js/app.js',
    admin: './static/src/js/admin.js'
  },
  output: {
    path: path.resolve(__dirname, 'static/js'),
    filename: '[name].bundle.js'
  },
  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all'
        }
      }
    }
  }
};
```

## 🚀 デプロイ自動化

### GitHub Actions での自動化

```yaml
# .github/workflows/deploy.yml
name: Deploy HADS Application

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Node.js
      uses: actions/setup-node@v2
      with:
        node-version: '16'
        
    - name: Build static assets
      run: |
        npm install
        npm run build
        
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v1
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ap-northeast-1
        
    - name: Deploy static files to S3
      run: |
        aws s3 sync static/ s3://your-bucket/static/ --delete
        
    - name: Deploy SAM application
      run: |
        sam build
        sam deploy --no-confirm-changeset
```

## 📊 パフォーマンスモニタリング

### キャッシュ設定

```bash
# ファイルタイプ別のキャッシュ設定
aws s3 cp static/css/ s3://bucket/static/css/ --recursive \
  --cache-control "max-age=31536000" \
  --content-type "text/css"

aws s3 cp static/js/ s3://bucket/static/js/ --recursive \
  --cache-control "max-age=31536000" \
  --content-type "application/javascript"

aws s3 cp static/images/ s3://bucket/static/images/ --recursive \
  --cache-control "max-age=31536000"
```

### 圧縮設定

```bash
# Gzip圧縮を有効化
aws s3 cp static/css/app.css s3://bucket/static/css/app.css \
  --content-encoding gzip \
  --content-type "text/css"
```

## 📋 ベストプラクティス

### 1. ファイル命名規則

```
static/
├── css/
│   ├── app.min.css          # メインスタイル
│   ├── vendor.min.css       # サードパーティCSS
│   └── components/
│       ├── navbar.css
│       └── footer.css
├── js/
│   ├── app.min.js           # メインスクリプト
│   ├── vendor.min.js        # サードパーティJS
│   └── modules/
│       ├── form-validation.js
│       └── carousel.js
└── images/
    ├── logo-192x192.png     # サイズを含める
    ├── hero-1920x1080.jpg
    └── icons/
        ├── user-24x24.svg   # SVGアイコン
        └── settings-24x24.svg
```

### 2. バージョン管理

```python
# settings.py でバージョン管理
STATIC_VERSION = "v1.2.3"

# テンプレートでの使用
# {{ static(master, 'css/app.css') }}?v={{ settings.STATIC_VERSION }}
```

### 3. セキュリティ対策

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowStaticFiles",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::bucket/static/*",
      "Condition": {
        "StringLike": {
          "s3:ExistingObjectTag/Environment": "production"
        }
      }
    }
  ]
}
```

## トラブルシューティング

### よくある問題

1. **静的ファイルが見つからない**
   - S3バケットの権限設定を確認
   - ファイルパスとURL設定を確認

2. **ローカルで静的ファイルが表示されない**
   - プロキシサーバーが正常に起動しているか確認
   - ポート設定を確認

3. **キャッシュが効かない**
   - Cache-Controlヘッダーの設定を確認
   - CloudFrontの設定を確認

## 次のステップ

静的ファイル管理を理解したら、以下のページで認証システムについて学習してください：

- [認証とCognito連携](./authentication.md) - ユーザー認証機能の実装
- [ローカル開発環境](./local-development.md) - 効率的な開発環境構築

---

[← 前: テンプレートシステム](./templates.md) | [ドキュメント目次に戻る](./README.md) | [次: 認証とCognito連携 →](./authentication.md)
