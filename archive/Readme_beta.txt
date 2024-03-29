-------------------------------------------------
-------------------------------------------------

　　PmxDressup

　　β版用追加Readme

　　　　　　　　　　　　　　　　　miu200521358

-------------------------------------------------
-------------------------------------------------

----------------------------------------------------------------
■　配布元
----------------------------------------------------------------

　・ニコニコミュニティ「miuの実験室」
　　　https://com.nicovideo.jp/community/co5387214
　・ディスコード「MMDの集い　Discord支部」
　　　https://discord.gg/wBcwFreHJ8

　※基本的にβ版は上記二箇所でのみ配布しておりますので、上記以外で見かけたらお手数ですがご連絡下さい。

----------------------------------------------------------------
■　β版をご利用いただくにあたってのお願い
----------------------------------------------------------------

・この度はβ版テスターにご応募いただき、ありがとうございます
　β版をご利用いただくのにあたって、下記点をお願いいたします。

・不具合報告、改善要望、大歓迎です。
　要望についてはお応えできるかは分かりませんが…ｗ

　・不具合報告の場合、下記をご報告ください
　　・β版の番号（必須）
　　・エラー発生時には、exeと同じフォルダにログファイルが出力されているので、そのログのエラー部分（必須）
　　・一般配布されているモデルや衣装の場合、お迎えできるURL
　　・ご報告はニコニコミュニティの掲示板にお願いします

・β版で作ったモデルの扱いは、リリース版と同様にお願いします。
　モデルの規約の範囲内であれば、どこに投稿していただいても、何に利用していただいても構いません。
　自作発言とツールの再配布だけNG。年齢制限系は検索避けよろしくです。

・β版を使ってみて良かったら、ぜひ公開して、宣伝してくださいｗ
　励みになります！公開先はどこでもOKです。
　その際に、Twitterアカウント（@miu200521358）を添えていただけたら、喜んで拝見に伺います

----------------------------------------------------------------
■　revision
----------------------------------------------------------------

PmxDressup_1.00.02_β04 (2023/10/08)
・子ボーンが出力対象である場合、親ボーンを出力するよう修正
・ボーンが紐付いていない剛体を出力するよう修正

PmxDressup_1.00.02_β03 (2023/10/01)
・体幹の移動Xと回転YZを無視するよう処理追加

PmxDressup_1.00.02_β02 (2023/10/01)
・首と頭の回転フィッティングを削除

PmxDressup_1.00.02_β01 (2023/09/30)
・IKリンクボーンが出力されており、かつIKボーンが出力されない場合があったのを修正
・お着替えモデル出力時のパス整合性判定がまだ作っていないフォルダの存在チェックをしていたので削除
・腕系ボーンの移動オフセット判定時に肩Cがない場合にエラーになる場合があったのを修正

PmxDressup_1.00.01_β12 (2023/09/10)
・握り拡散系はフィッティング・出力しないようスキップ処理追加
・PMXモデル名にファイル出力出来ない文字が入っていた場合に除去するように修正

PmxDressup_1.00.01_β11 (2023/09/08)
・お着替えモデル出力時にIKボーンの出力判定が間違っていたので修正

PmxDressup_1.00.01_β10 (2023/09/06)
・上半身3を準標準チェック対象に追加
・上半身や下半身などのボーン位置調整を行う際の基準ボーンから頭・首を除外（代わりに上半身2などを使用）

PmxDressup_1.00.01_β09 (2023/09/06)
・靴サイズ決めのエラーハンドリング追加

PmxDressup_1.00.01_β08 (2023/09/04)
・靴の大きさを人物と衣装の靴底（Z方向の幅）の比率で決めるよう処理修正

PmxDressup_1.00.01_β07 (2023/09/04)
・エラーハンドリングが漏れていたので追加

PmxDressup_1.00.01_β06 (2023/09/03)
・準標準外フィッティングの時のNoneチェック追加

PmxDressup_1.00.01_β05 (2023/09/03)
・足首などグローバルで個別調整する場合にY回転が左右同一の回転ではなかったのを修正

PmxDressup_1.00.01_β04 (2023/09/03)
・個別調整ボーンの条件として「個別調整リストに親が含まれる場合、親が準標準であれば登録判定対象とする」を追加

PmxDressup_1.00.01_β03 (2023/09/03)
・全ての親がないPMXモデルなども付けられるよう調整

PmxDressup_1.00.01_β02 (2023/09/02)
・衣装のモーフが表示枠に入らない場合があったのを修正（突き合わせ条件が間違っていた）
・SDEFパラメーター再計算処理追加
・準標準ボーンと同じ位置にある準標準外ボーンを、準標準と同じ場所に配置するよう調整
・袖IKなどの準標準外フィッティングを調整
　（準標準までのボーンと同じ位置にある準標準外を、準標準に合わせるよう調整）

PmxDressup_1.00.01_β01 (2023/08/26)
・猫耳などパーツのフィッティングの時にエラーになっていたのを修正
　・存在しないボーンの必須チェックが走ってた（不要なので削除）

PmxDressup_1.00.00_β49 (2023/08/18)
・首のローカルXスケールを上半身2に準拠するよう修正
・移動調整がある場合に移動量が1e-2以下である場合、（縮尺ベースの補正値取得）計算が狂うので調整対象が意図する
・胸を上半身2とかの個別調整の対象外
・首と頭の移動フィッティングを削除（首の位置が自由なので組み合わせによっては潰れる）

PmxDressup_1.00.00_β48 (2023/08/18)
・準標準外のスケール調整
　・親もしくは付与親が準標準である場合、親のローカルスケールを流用するよう調整
　・親が準標準外の場合は親のローカルスケールXをグローバルXYZに割り当てる
・接地ロジックでうまく接地出来ない場合がある（足IKが足首にないモデルの場合）のを修正

PmxDressup_1.00.00_β47 (2023/08/17)
・モーフ変形機能
　・材質モーフの変動量が反映されていなかったのを修正
・コピー元材質のダイアログ文言修正
・色補正でテクスチャが無い場合、拡散色と環境色を補正するよう処理追加
・準標準外のボーンが不要な回転を除外するよう修正
・保存時に足Dの補正処理で正しいボーンINDEXを参照できてなかった不具合を修正（#474）
・処理チューニング（高速化）

PmxDressup_1.00.00_β46 (2023/08/12)
・モーフ変形機能追加
　・手袋を消したりなどのモーフを適用させた状態でお着替えを出力できるよう機能追加

PmxDressup_1.00.00_β45 (2023/08/09)
・MMD系共通処理更新

PmxDressup_1.00.00_β44 (2023/08/03)
・処理完了音が動かなくなっていたので修正

PmxDressup_1.00.00_β43 (2023/08/02)
・ライブラリアップデートに伴い開発環境再構築
・ベース処理cython対応
・個別調整縮尺XZのリンクを画像ボタンに変更

PmxDressup_1.00.00_β42 (2023/07/28)
・ベース処理チューニング
・プレビュー機能高速化

PmxDressup_1.00.00_β41 (2023/07/23)
・小さいサイズのモデルにも適用できるよう計算タイミングを修正
・衣装モデル側にしかいないボーンの表示枠が1ボーンごとに作られていたのを衣装側の表示枠に合わせてまとめて設定するよう修正
・非透過度ショートカットボタンに 0.2 を追加

PmxDressup_1.00.00_β40 (2023/07/23)
・ウィンドウリサイズ機能追加

PmxDressup_1.00.00_β39 (2023/07/22)
・ローカルスケーリングの長さ判定時に準標準ボーンがなかった場合にスルーするよう、エラーハンドリング追加
・テクスチャ補正時に画像上下反転を元に戻すのを忘れていたので修正

PmxDressup_1.00.00_β38 (2023/07/22)
・人物や衣装と同じパスもしくは同階層に出力パスを変更した場合に、テクスチャなどを上書きする危険性があるため、エラーとするようハンドリング追加
・出力ファイルパスが未設定の場合にデフォルト出力パスを設定するよう処理追加
・エラーメッセージ整理
・フィッティング調整
　・ウェイトの厚みを計算する対象に準標準ボーンを親に持つ準標準外ボーンも対象とするよう追加
　・事前にボーンの内部位置を変更する際のウェイト調整を体幹のみ行い、四肢は位置を調整してもウェイトは変更しないよう変更
　・首根元を上半身2の子ボーンとして個別調整できるよう変更
　・手首にグローバルスケールをかけるよう変更（手首と指はそれぞれ別にローカルスケーリング可能）
・材質補正UI変更
　・痣やタトゥーなどがある場合に材質設定の複製で意図した肌色などがコピーできない場合があるため、個別に色指定と材質定義ができるようUI変更

PmxDressup_1.00.00_β37 (2023/07/14)
・テクスチャの反転処理を復活（描画時の法線が逆に計算されてしまう）
・足IKの事前フィッティングで人物側にないボーン（操作中心等）であればスルーするよう判定追加

PmxDressup_1.00.00_β36 (2023/07/12)
・IKターゲットボーンの位置再計算条件をミスっていたので修正

PmxDressup_1.00.00_β35 (2023/07/12)
・肌材質設定コピー処理追加
　衣装モデルと人物モデルのそれぞれ肌材質に対して「肌材質として設定を共有する」のチェックをONにすると、
　人物モデルの肌の色味に似るように衣装モデルの肌テクスチャに対して補正をかける事ができます
・選択部位のウェイト表示機能追加
　腕などの部位を選択し、「ボーンウェイト表示」チェックをONにすると、該当部位が扱えるメッシュだけを表示し、他の非透過度を下げます
・フィッティングロジック修正
　・肩が下がり気味に補正されてしまう不具合を修正
　　・肩ボーンの位置補正、ウェイト調整
　　・肩根元ボーン（システム用）追加（出力時には除外します）
　・頭ボーンがない場合に頭部装飾がズレる不具合を修正
　・準標準の間に挟まっている準標準外ボーンのズレに対応するため、ボーン計算順に合わせて計算するよう順番変更
　・準標準外の移動オフセット計算方法修正
　・つま先ＩＫとそのターゲットボーンのＹ位置を０に固定
・出力先ディレクトリの変更が動かない場合があったのを修正
・出力パス変更（出力日時をディレクトリ側に移動）
・衣装の腕など体を覆う箇所のメッシュが準標準ボーン以外にウェイトが乗っている場合、サポート対象外となる旨をリドミに追記
・ひざのボーンの長さを変えた時などで、お着替え結果で足ＩＫの位置がズレていたのを修正

PmxDressup_1.00.00_β34 (2023/07/08)
・MMDエンジン対策で無限ループにならないよう上限設定
・お着替え結果出力ロジックの不具合修正
　・ローカル軸が正常に計算できない場合があったのを修正
　・表示枠にすべての表情を入れていたので、人物と衣装で表示枠に入っている表情だけ入れるよう修正
　・IKのターゲットやリンクが出力対象である場合、IKボーンも必ず出力するよう修正
　・外部親キーが入って無かったのを修正
・握り拡散ボーンを個別調整対象外に変更
・握り拡散ボーン、調整ボーンが動くように調整
・準標準の先ボーンの判定処理を狭めるよう修正

PmxDressup_1.00.00_β33 (2023/07/06)
・お着替えモデルのボーン出力処理修正
・フィッティング処理を全体的に修正
　・腕は腕から手首までの角度のみで割り当てる（ひじの角度を入れると変に曲がる衣装がある）
　・足のフィッティング計算式修正（足首を足IKの位置で仮置きしたうえでひざ位置を計算する）
　・末端の回転キャンセル調整
　・システム用ボーン（首根元と足中心）の再計算追加
　・フィット調整時にローカルスケーリング加味
・胸追加時にボーン設定を再セットアップし忘れてたので修正
・衣装が歪んでしまう場合があるのを修正
　・体幹系のX方向を0に強制補正（歪みの原因）
　・左右は平均値を取って変形させる
・関連ボーンINDEXリストの取得方法を修正
・IK計算結果保持クォータニオンが設定されている場合、IK計算フラグの有無に関わらず回転量計算処理に含めるよう修正
・フィッティング前にボーン位置そのものを調整する処理をグローバル位置からローカル位置で計算するよう修正
　・A→T変換などの時にグローバル位置での計算だと逆にズレが大きくなってしまうため
・上半身の再計算時の基準を首根元から足中心に変更
【残件】
・握り拡散、調整ボーンなど、複雑なボーン構造の場合の対応
・疑似AスタンスなどIKで動きが決まる場合の対応
・シェーダーのダウングレード

PmxDressup_1.00.00_β32 (2023/06/27)
・MMD系共通処理からDressup用の属性を取り出して、Dressupリポジトリ側で拡張定義するよう修正
・ファイルを入れ替えようとするとクラッシュする（OpenGLのdelete処理エラーっぽい）
　・Toonテクスチャ削除処理の直接DEL処理を廃止
・腕の構造が複雑な場合（準標準ボーンの間に準標準外ボーンがあるような場合）のフィッティング
　・出力時に準標準ボーンの親が準標準ではない場合、準標準ボーンを基準に親を調整しなおすよう修正
・フィッティング用BoneSettingを共通ライブラリから個別設定に分離
・足のフィッティング処理を修正
　・足FKを調整した後に結果を足Dにコピーしてズレないように
　・足IKは足首Dの後にIK OFF時の足首の位置に合わせるように
・胸の個別調整ボーン追加
　・「左胸」「右胸」ボーンが人物にある場合、衣装にも同様のボーンを追加し、個別調整選択肢に追加
　　・デフォルトでのローカルスケーリングは行いません
　　・人物の胸ボーンはウェイトを持ってなくても構いません
　　・衣装側のポリ割り自体は変えてないので、ポリ割りによっては変形が綺麗になりません
・エラー時のログや設定ログに出力対象材質名一覧を追記
・単ボタンを押した後、選択材質を変えたりしたら単フラグをOFFにするようフラグ処理変更
・ローカル縮尺・回転キャンセル外対象に指を追加
・個別調整の軸方向を変更：　X軸：横方向、Y軸：長さ方向、Z軸：奥行き方向
・手首のローカル回転を指でキャンセルしないよう調整
・指のローカルスケールが残っていたので削除
・保存時に足Dを足FKに揃える
・表示枠に追加ボーンを設定してなかったのを追加するように修正
・必ず追加する準標準ボーンに「肩P」「グルーブ」を追加
・準標準ボーンのウェイトの塗り方を調整
・ローカルスケーリングをXZの平均値で処理するよう修正
・ボーンラインと全材質の単フラグを使えないように
・ボーン位置を衣装モデルに合わせるフラグを追加

PmxDressup_1.00.00_β31 (2023/06/19)
・自身が準標準ボーンか、だけでなく準標準ボーンまでのボーン構成の中にあるか、をチェック
・肩のスケール対象から肩Pを削除（移動だけの対象に移動、肩Cも同様）
・カメラの回転計算をQuaternionからEulerに変更
・選択したボーンをハイライトさせる機能追加
・お着替えモデル出力時の剛体サイズ再計算処理が人物剛体の方を参照していたのを衣装剛体を参照するよう修正
・衣装側が表示先がなくて、人物側に表示先がある場合、表示先ボーンの位置を変形後の位置に合わせる
・コメントに入れていた個別調整の詳細パラメータを設定ファイルとして別出力するよう変更
・材質の非透過度を0にする「0.0」ボタン、1にする「1.0」ボタン追加
・設定を変更する毎に出力ファイルパスを更新するよう修正
・Vroid2Pmx経由（上半身3がある）モデルを人物モデルにした場合のフィッティングを修正
・足の個別調整が効かない場合がある不具合を修正
・ローカルスケーリングをYZ（横幅と奥行き）別々に適用するよう変更
・上半身、下半身を一括で動かせるよう個別調整に腰追加
・個別フィッティング調整
　・すべてのボーンに対してグローバルスケーリングを行った状態でフィッティング実行
　・足IKは足首より先にフィッティングさせる（足首の安定）
・pyinstaller のビルド環境再構築
【残件】
　・腕の構造が複雑な場合（準標準ボーンの間に準標準外ボーンがあるような場合）のフィッティング
　・人物モデルに胸ボーンがある場合のフィッティング
　・ファイルを入れ替えようとするとクラッシュする（OpenGLのdelete処理エラーっぽい）


PmxDressup_1.00.00_β30 (2023/06/17)
・ログ追加
・MShaderの削除処理時にtry-except追加
・グループモーフが出力されない場合がある不具合を修正
・変形階層の判定が失敗する場合がある不具合を修正
・カメラの上方向の計算処理が間違っていたのを修正

PmxDressup_1.00.00_β29 (2023/06/15)
・グローバルスケールの計算をmeanから maxとmeanの中間に変更
　・ボーンの長さだけだと小さくスケーリングされやすい
　・体幹は min と mean の中間とする
・スケーリングを行う時のカテゴリ整理（ウェイトの乗り方や軸方向によってかなりローカル位置計算時に差が出るため）
　・肩を腕から肩に変更
　・足首・足先EXを足から足首に変更
　・手首を腕から手首に変更
・準標準以外のIKのターゲットボーンをフィッティングさせられるよう修正
・一旦指の移動フィッティング削除
・単一材質のみを表示する「単」ボタン追加
・調整ボーンも含められるよう関係ボーンリスト修正
・個別調整時に肩P・肩Cも調整するよう修正
・準標準外の装飾ボーンを個別調整できるようプルダウンに追加
・VMD計算時のキャッシュ処理の有効でないものを廃止（fno_poses、fno_scales）
・上半身、下半身もボーン位置調整対象に追加
・デバッグ用にコンソールありexeを追加
　・β29.exeを開いた際に "Unhandled exception in script" というエラーが出て開けない場合、こちらのexeを開いてみてください
　　コンソール（黒いウィンドウ）に起動時のログが出ますので、その全てをコピーして、コミュニティの掲示板でご報告お願いします

PmxDressup_1.00.00_β28 (2023/06/11)
・出力時の変形階層を自身・親ボーン・付与親ボーンのうち最大の変形階層に合わせるよう修正
・手動調整モーフで上半身をローカルスケーリングしたときに上半身2も同じ値でローカルスケーリングできるようモーフオフセット追加（他も同様）
・ローカルスケーリング計算元となるボーンと頂点のローカル位置関係を求める処理を修正
・個別調整欄の処理を共通化
・足周りのフィッティング調整
　・足D系列は足FKに合わせる
　・足FK系列は回転しないで、足D系列でのみ回転させて変形させる
・保存時のボーン位置置き換え処理に人物ウェイト有無判定を追加
・準標準以外のスケールは親となっている上半身または下半身のグローバルスケールを適用するよう変更
・準標準に繋がってる準標準以外のグローバルスケールは個別調整時にも適用するよう変更
・出力お着替えモデルのファイル名にモデル名を使用するよう変更
【残課題】
　・疑似AスタンスなどIKで動きが決まる人物モデルがベースの場合に出力後のお着替えモデルで変形が変になる場合がある（例：ISAO式）

PmxDressup_1.00.00_β27 (2023/06/07)
・ローカルスケーリング修正
・マージ出力時のボーン出力有無判定修正
・再フィット処理削除（無理に再フィットさせようとすると変形が汚くなる）
・接地処理を出力直前に常に行うよう処理移動

PmxDressup_1.00.00_β26 (2023/05/28)
・リファクタリング
・左腕・左足のスケーリング計算が間違っていたので修正
　（右の計算をクリアしてなかった）
・再フィット計算が無効になっていたので有効に修正

PmxDressup_1.00.00_β24 (2023/05/22)
・テクスチャ複製処理でバッティング時の処理追加
・追加UVが指定されてる場合のPMX保存処理修正
・お着替えモデル出力時のログ追加
・衣装ボーンの接続不具合修正
・接地ボタン追加（衣装の靴底が地面に付くように全体のY位置を調整）
　・これに伴い人物モデルも変形後の形で出力するよう修正
・レイアウト調整
・スライダーの有効範囲調整
・再生ボタンを押すと、停止ボタンまで無効化されてしまうのを修正
・再生ボタンのラベル修正

PmxDressup_1.00.00_β23 (2023/05/22)
・保存時のモデルデータ存在チェック追加
・出力ファイルパスが無効な場合、デフォルトパスを再設定するよう修正
・スレッド停止処理追加
・お着替えモデル出力時に、衣装モデルから持ってきたオブジェクトの名前に「Cos:」を追加
・名前バッティング時の処理追加
・ツールレイアウト調整

PmxDressup_1.00.00_β22 (2023/05/21)
・必須ボーンが足りないなどでエラーになった場合にファイルタブのボタンを有効にするよう修正
・足首の位置を衣装側のボーン位置で補正
・ジョイント出力まで一通り

PmxDressup_1.00.00_β21 (2023/05/21)
・エラー発生時のログ出力先をexeのある場所に修正
・お着替えモデル出力時に表示枠追加（MMDで表示できるようになった）
・その他細かいバグ修正

PmxDressup_1.00.00_β20 (2023/05/21)
・お着替えモデル出力機能追加（ボーンまで）
・個別フィッティングの最小値を変更
・FloatSliderのイベントハンドリング修正
・クリアボタン時の挙動修正
・個別フィッティングのスケールと回転をローカル軸に沿うよう修正
　・スケールと回転は子には伝播させない
　・移動はグローバル

PmxDressup_1.00.00_β19 (2023/05/14)
・個別フィッティング機能追加
　・キャンセル機能はあえて付けてない（自動キャンセルさせると混乱した）

PmxDressup_1.00.00_β18 (2023/05/13)
・腕捩り系を上半身2と同じように人物モデルの相関位置に配置するよう調整
　・腕捩り系を必須ボーン（なかったら追加するボーン）に追加
・ボーンラインのデフォルト透過度を0.5に変更
・非透過度が小さい材質の描画を行うため、不透明時のみアルファテストをONにするよう判定追加
・頭のスケーリングをOFF

PmxDressup_1.00.00_β17 (2023/05/13)
・再生時にフォームパーツをdisableに切り替える処理を追加
・フィッティングの計算順番を修正
　・移動→回転→スケールの順番で計算し、順番に変形を適用させて次のボーンのフィッティングを行う
・頭部装飾用ボーンを挿入し、頭アクセを一括で動かせるよう修正（操作処理自体は未実装）
・衣装側の上半身2の位置を人物モデルの相関位置に配置
　・上半身から見た上半身2の位置と、首から見た上半身2の位置の中間地点に配置する

PmxDressup_1.00.00_β16 (2023/05/06)
・疑似AスタンスなどIKで動きが決まるタイプの人物モデルでフィッティングに失敗していたのを修正

PmxDressup_1.00.00_β15 (2023/05/06)
・ルートスケーリングを削除（移動にスケーリングをかけない）
・頭のスケーリングロジックを修正

PmxDressup_1.00.00_β14 (2023/05/06)
・ログレベル修正
・全材質透明化機能追加
・カメラが後ろに回ったときにホイールの回転が逆方向になるのを修正
・中ホイールでの移動時にホイールの回転を加味するよう修正
・スピンコントロールでEnterキーを押下したときに変化を反映させるよう修正
・人物モーションと衣装モーションと別々のプロセスで実行するよう修正
・オリジナルデータを別で保持するよう修正
・人物・衣装いずれかに準標準ボーンが足りない場合、足りない方に追加するよう機能追加
・ロジック系をusecaseに分離

PmxDressup_1.00.00_β13 (2023/04/30)
・引数あり起動を、ショートカット起動からバッチ起動に変更
・スケーリングありボーンモーフ追加
・ログあり版でログが正常に出力されていなかったのを修正
・マルチプロセスアニメーションの不具合対応
　・透明度変更時にon_playが走る場合があったのを修正
　・multiprocessing.popen_spawn_win32.Popenをforkして、pyinstaller用マルチプロセス処理に修正

PmxDressup_1.00.00_β12 (2023/04/23)
・追加UVがあった場合に後ろの方のメッシュ変形がおかしくなる不具合を修正
・捩りのフィッティングがズレてたのを修正
・親までをフィッティングさせた上で改めてフィッティング先のボーン位置を求めるよう修正

PmxDressup_1.00.00_β11 (2023/04/18)
・透過度を変えた場合にはボーンデフォーム計算を行わないよう修正
・Playボタンでモーションを停止させた時にProcessも停止するよう処理追加

PmxDressup_1.00.00_β10 (2023/04/18)
・ログ追加

PmxDressup_1.00.00_β09 (2023/04/17)
・材質の透過度の計算が間違っていたので修正
・アニメーションをマルチプロセスで処理
・フィッティングの角度計算が間違っていたので修正
・衣装の装飾用ボーン（標準・準標準以外のボーン）のボーンフィッティング追加

PmxDressup_1.00.00_β08 (2023/04/15)
・材質の透過度を個別に変更できる機能追加
・人物モデルと衣装モデルのボーンの角度差を加味したボーンフィッティング処理に修正
　・必須ボーンチェック追加（センター、上半身、下半身）
　・準標準ボーンの範囲外の場合、とりあえず縮尺対象外
　・モデルによっては変形が汚くなるので、頂点スムージング検討中
・描画に失敗した時のエラーメッセージ表示
・処理完了時のサウンド
・モーションのみを切り替えた場合、人物・衣装のフィッティングはそのままで切り替えられるよう機能追加

PmxDressup_1.00.00_β07 (2023/04/09)
・ボーン描画機能追加

PmxDressup_1.00.00_β06 (2023/04/09)
・デバッグ版でのみ、変形モーフ付き衣装モデル出力機能追加
・ボーン縮尺の計算式を修正
・材質OFF機能追加（頂点モーフ）
・スケール付きモーション再生機能

PmxDressup_1.00.00_β05 (2023/04/08)
・モデル・モーション再読込に対応
・衣装モデルの縮尺合わせをボーンモーフに変更
