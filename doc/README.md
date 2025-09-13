# WAMBDA ドキュメント

WAMBDA (h-akira AWS Develop with Serverless) は、AWS Lambda上で動作するサーバレスWebアプリケーションフレームワークです。

## 📚 ドキュメント目次

### 🚀 はじめに
- [概要とフィロソフィー](./overview.md)
- [インストールと初期設定](./installation.md)
- [クイックスタート](./quickstart.md)

### 📖 基本ガイド
- [プロジェクト構造](./project-structure.md)
- [URLルーティング](./url-routing.md)
- [ビューとハンドラー](./views-handlers.md)
- [テンプレートシステム](./templates.md)
- [静的ファイル管理](./static-files.md)

### 🔧 高度な機能
- [認証とCognito連携](./authentication.md)
- [ローカル開発環境](./local-development.md)
- [Mock機能とテスト環境](./mock.md)
- [デプロイメント](./deployment.md)
- [コマンドラインツール](./cli-tools.md)

### 🛠️ 実践的な使い方
- [サンプルアプリケーション](./examples.md)
- [ベストプラクティス](./best-practices.md)
- [トラブルシューティング](./troubleshooting.md)

### 📄 リファレンス
- [API リファレンス](./api-reference.md)
- [FAQ](./faq.md)

## 🤝 貢献

WAMBDAフレームワークの改善にご協力いただける場合は、[GitHubリポジトリ](https://github.com/h-akira/wambda)をご確認ください。

## 📝 ライセンス

このプロジェクトは適切なライセンスの下で公開されています。

---

> **注意**: WAMBDAはAWS SAMを基盤とし、単一のLambda関数でWebアプリケーション全体を動作させるアーキテクチャを採用しています。従来のサーバーベースのフレームワークとは設計思想が異なりますので、使用前に[概要とフィロソフィー](./overview.md)をお読みください。
