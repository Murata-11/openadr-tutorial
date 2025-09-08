# 9. 伝送プロトコル

OpenADR 2.0 は、さまざまな導入シナリオに対応するため、少数の伝送プロトコルをサポートしています。
2.0b VEN（Virtual End Node）は HTTP または XMPP をサポートするか、または両方をサポートすることができます。
VTN（Virtual Top Node）は HTTP と XMPP の両方をサポートしなければなりません。

## 9.1. シンプル HTTP

OpenADR 2.0 (a/b) におけるシンプル HTTP とは、HTTP POST over TLS を使用して OpenADR ペイロードを伝送する HTTP 実装を指します。

### 9.1.1 PUSH と PULL の実装

#### 9.1.1.1 PUSH の定義

PUSH モードでは、メッセージは VTN から VEN に送信されます（プッシュされる）。
PUSH を利用するためには、VEN が HTTP URI エンドポイント（HTTP サーバー） を公開しておく必要があります。これにより、VTN は oadrDistributeEvent などのリクエストを送信できます。
この方式は、OpenADR を HTTP 上で実行する最も効率的な方法ですが、VEN がネットワークファイアウォールの背後に存在する可能性があるため、技術的な課題が発生します。

#### 9.1.1.2 PULL の定義

PULL モードでは、すべての操作は VEN から VTN に対して開始されます。これは「ポーリング」モードとも考えられ、VEN が定期的に VTN に更新を問い合わせます。
PULL モードを使うことで、VEN 側に HTTP サーバーを設置する必要がなくなり、ファイアウォールによる制限を回避できます。

ただし、PULL モードには以下のような制限があります：

遅延（ポーリング頻度が限られるため）

帯域幅の増加

さらに、PULL モードでは一部の操作を完了するために「二段階の実行」が必要となる場合があります。これは、VEN 側が HTTP リクエストを開始する仕組みに起因します。

PUSH モードの場合
VTN は oadrDistributeEvent 操作を通じて VEN に新しいイベントを通知します。
このとき、VTN は oadrDistributeEvent ペイロードを含むリクエストを送信し、VEN は HTTP 200 で応答した後、非同期に oadrCreatedEvent を返します。

PULL モードの場合
VEN は VTN に oadrPoll を送信してイベントを要求します。
これに対して VTN は oadrDistributeEvent ペイロードを含むレスポンスを返します。
VEN はレスポンスを解析した後、新しいイベントの作成を確認するために、さらに oadrCreatedEvent 操作を実行する必要があります。
