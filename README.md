# HADS
## Overview
HADS (h-akira AWS Develop with Serverless) is a framework to develop serverless web applications on AWS.  
Although this framework is a successor to [HAD](https://github.com/h-akira/had), 
there are some cases where it is recommended to continue using HAD because the philosophy is very different.

## Philosophy
- Use SAM
- One Lambda
- Static files are distributed from S3
- Test Locally
- Like Django

## Structure
The AWS configuration for a system built using HADS is shown below. 
Only Lambda and API Gateway are created directly by HADS. 
Although S3 is not created, 
it is possible to synchronize static files using HADS commands.
Other resources are created separately or added to SAM's template.yaml by developper.
![structure](images/structure.png)  
The Lambda program structure is shown below. 
It is similar to Django, with urls.py, views.py, and template at its core. 
The same Lambda is called from API Gateway regardless of the path. 
When the handler is executed, the view function is passed by the routing function after the initial settings and authentication.
The view function is executed in the handler and the result is returned.
![lambda](images/lambda.png)  

## 📚 ドキュメント

詳細なドキュメントは [doc](./doc/README.md) ディレクトリをご覧ください。

### 🚀 クイックスタート
- [インストールと初期設定](./doc/installation.md)
- [クイックスタートガイド](./doc/quickstart.md)

### 📖 基本ガイド
- [プロジェクト構造](./doc/project-structure.md)
- [URLルーティング](./doc/url-routing.md)
- [ビューとハンドラー](./doc/views-handlers.md)
- [テンプレートシステム](./doc/templates.md)

### 🔧 高度な機能
- [認証とCognito連携](./doc/authentication.md)
- [ローカル開発環境](./doc/local-development.md)
- [デプロイメント](./doc/deployment.md)

## Usage

HADSを使った基本的な開発手順：

1. **プロジェクト初期化**
```bash
hads-admin.py --init
```

2. **ローカル開発**
```bash
cd my-project
hads-admin.py admin.json --local-server-run proxy
```

3. **AWSデプロイ**
```bash
hads-admin.py admin.json --build --deploy
```

詳細な使用方法については[ドキュメント](./doc/README.md)をご参照ください。

## SampleProject
The following is a sample project that uses HADS.
- [HadsSampleProject](https://github.com/h-akira/HadsSampleProject)

## Development Schedule
The following features will be added later date:
- Genarete SAM and other templates
