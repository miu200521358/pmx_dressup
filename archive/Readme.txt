----------------------------------------------------------------
----------------------------------------------------------------

　「PmxDressup」

　　ver1.00.02

　　　　　　　　　　　　　　　　　miu200521358

----------------------------------------------------------------
----------------------------------------------------------------


　この度は拙作をDLしていただき、ありがとうございます。
　お手数ですが以下をご確認のうえ、ご利用ください。

----------------------------------------------------------------


----------------------------------------------------------------
■　概要
----------------------------------------------------------------

　指定したモデルに指定した衣装を体形に合わせてフィッティングするツールです

　・ボーンの長さと身体の厚みに基づいた自動フィッティング
　・人物材質を半透明にして、体型を確認しながら細かい調整が可能
　・ボーンや剛体・ジョイントの関係を調整してお着替え結果出力
　・材質ごとの色合わせや設定のコピー

　下記ボーンをお着替えモデルに作成します
　　・全ての親, 上半身2, 腕捩, 手捩, 足先EX

　【事前に必要な作業】
　　・材質単位でお着替えモデルへの出力有無を設定するため、出力したい頂点としたくない頂点が同じ材質にある場合、材質を分けておいてください

　【出力後に手動で必要な調整】
　　・剛体のグループと非衝突グループの設定
　　　　→　衣装が暴れる場合、衣装の根元の剛体を接触している身体の剛体と非衝突にしてください
　　・下側の頂点の削除
　　　　→　穴あきにならない範囲で削除した方が、頂点の突き抜けがなくなり、モデルが軽くなります

　【注意事項】
　　・変形を綺麗にするため、衣装モデルのウェイトを若干弄ってます
　　　ウェイト操作が許可されていない衣装モデルにはご利用いただけません
　　・衣装の腕など体を覆う位置にあるメッシュが準標準ボーン以外にウェイトが乗っている場合、サポート対象外となります
      （ある程度はフォローしてますが、準標準外ボーンを操作して縮尺などを弄っていただく場合も多いと思います）


----------------------------------------------------------------
■　配布動画
----------------------------------------------------------------

YouTube
https://youtu.be/_4Ikx19ISjA

ニコニコ動画
https://www.nicovideo.jp/watch/sm42645182


----------------------------------------------------------------
■　コンテンツツリー用静画
----------------------------------------------------------------

　PmxDressup - コンテンツツリー用
　https://seiga.nicovideo.jp/seiga/im11209493

----------------------------------------------------------------
■　同梱ファイル
----------------------------------------------------------------

　・PmxDressup_x.xx.xx.exe　…　ツール本体（言語別バッチあり）
　・Readme.txt　　　　　　　　…　Readme
　・VMDサイジングWiki　　　　 …　Wikiへのリンク
　・コンテンツツリー用静画　　…　コンテンツツリー用静画へのリンク
　・メッシュ補填用素体　　　  …　素体（VRoid製）


----------------------------------------------------------------
■　動作環境
----------------------------------------------------------------

　Windows10/11 64bit
　OpenGL 4.4 以上が動くCPUもしくはGPU


----------------------------------------------------------------
■　起動
----------------------------------------------------------------

・基本的にはexeをそのまま起動していただければ大丈夫です。

・翻訳版は該当言語のバッチをダブルクリックしてください。
　・英語版　　　　…　-en.bat
　・簡体中国語版　…　-zh.bat
　・韓国語版　　　…　-ko.bat

・ファイル履歴は、「history.json」をexeと同じ階層にコピペする事で移行可能です。


----------------------------------------------------------------
■　基本的な使い方
----------------------------------------------------------------

 1. ファイルタブで人物モデル、衣装モデルを指定します（モーションは任意ですが重いです…）

 2. 設定タブを開きます
    - 一度設定タブを開いたら出力ボタンが押せるようになっています

 3. 設定タブでは、身長や体格などの基本的なフィッティングが済んだ状態のお着替えモデルが左側に表示されます
    - 右上(左)では、材質の出力有無を非透過度で指定できます
       - 非透過度が1未満の材質は出力しませんので、不要な材質の非透過度を下げてください
    - 右上(右)では、人物・衣装のモデルのモーフ適用を指定できます
       - 0より大きい値が指定されたモーフを適用した状態でお着替え結果を出力します
    - 右下ではボーン種類ごとの調整ができます
       - 縮尺X … ボーンの向きに対して上方向
       - 縮尺Y … ボーンの向き方向
       - 縮尺Z … ボーンの向きに対して奥行き方向

       - 回転X … ボーンの向きに対して前後方向
       - 回転Y … ボーンの向き方向(捩り回転)
       - 回転Z … ボーンの向きに対して上下方向

       - 移動X … グローバルX方向
       - 移動Y … グローバルY方向
       - 移動Z … グローバルZ方向

    - 同じボーン名に対して、人物と衣装の両方でウェイトが塗られたメッシュがある場合、位置などは基本的には人物側に合わせて出力します
      ただし、「ボーン位置を衣装モデルに合わせる」にチェックを入れると、強制的に衣装側のボーン位置に合わせて出力できます
      特に手首から先（指）に関してはあえてフィッティングを行っていないので、適宜選択してください

    - 人物・衣装の材質ごとに色合わせする事ができます
       - ペンキアイコン　…　画面上の色をスポイトのように抽出して色を指定できます
       - 色バー直接実行　…　Windows標準カラーパレットで任意の色を指定できます

 4. 調整フィッティングが終わったら、ファイルタブに戻って「お着替えモデル出力」ボタンを押してください
    - お着替えモデル出力先パスに材質・ボーン・剛体などを適宜調整したモデルを出力します
    - お着替え結果で元モデルのファイルやテクスチャなどを上書きする危険性がある場合、出力を中断します
    - 握り拡散ボーンなど一部ボーンは階層などの計算が難しいため、出力対象外にしています

 【おまけ】
   「メッシュ補填用素体」フォルダ内のモデルデータは VRoid Studio で私が作成した素体モデルです。
   首やひじより上など、人物モデルにメッシュが足りない場合、このモデルを衣装モデルとして読み込み、
   フィッティング結果を出力することで必要なメッシュが補填された人物モデルを使うことができます。
   特に制限事項などはありませんので、使えそうならご利用ください。



----------------------------------------------------------------
■　問題が起きた場合
----------------------------------------------------------------

　・解凍ファイルの文字化け
　・マカフィーでウィルスが入っていると検知されてしまう
　といった問題が起きた場合、下記ページを参照して、解決できるかご確認ください。（VMDサイジングのFAQページです）

　https://github.com/miu200521358/vmd_sizing/wiki/03.-%E5%95%8F%E9%A1%8C%E3%81%8C%E8%B5%B7%E3%81%8D%E3%81%9F%E5%A0%B4%E5%90%88

　それでも解決出来ない場合、下記コミュニティにてご報告ください。


----------------------------------------------------------------
■　コミュニティのご案内
----------------------------------------------------------------

　ニコニコミュニティ：https://com.nicovideo.jp/community/co5387214

　　VMDサイジングやモーションサポーターなど、自作ツールに関する諸々実験室
　　一足早くβ版を試していただくことができます。
　　ツールがうまく動かない場合のフォローなども行えたらいいなーと思ってます。
　　一応クローズドですが自動承認なのでお気軽にどうぞ


----------------------------------------------------------------
■　使用条件 他
----------------------------------------------------------------

　《必須事項》

　　・お着替えしたモデルを公開・配布する場合は、クレジットの明記のご協力をお願い致します
　　・ニコニコ動画の場合、コンテンツツリーへツリー用静画（im11209493）を登録してください
　　　※コンテンツツリーに親登録していただける場合、クレジット記載は任意です
　　・モデルを不特定多数に配布される場合、配布告知元（動画等）にだけクレジット明記/コンテンツツリー登録をお願いいたします
　　　※該当モデルを使用した作品にクレジット記載を求める必要はありません

　《任意事項》

　　本ツールおよび衣装を設定したモデルに関して、元々のモデルの規約の範囲内で、以下の行為は自由に行って下さい

　　・お着替えしたモデルの調整・改変
　　　※配布モデルの場合、規約で改変が許可されている事を確認してください
　　・動画投稿サイト、SNS等へのモデル使用動画投稿
　　　・進捗等で生成した衣装設定が入ったモデルそのままを投稿することも問題ありません
　　　・ただし、元々のモデルの規約で投稿先や年齢制限等の条件が規定されている場合、このツールでお着替えしたモデルもそれに準じます
　　・お着替えモデルの不特定多数への配布
　　　※自作モデルもしくは不特定多数への配布が許可されているモデルのみ

　《禁止事項》

　　本ツールおよび生成したモデルに関して、以下の行為はご遠慮願います

　　・元々のモデル等の規約範囲外の行為
　　・完全自作発言
　　・各権利者様のご迷惑になるような行為
　　・他者の誹謗中傷目的の利用（二次元・三次元不問）
　　・作者詐称、転載

　　・下記条件は禁止事項ではありませんが、ご配慮をお願いいたします
　　　『過度な暴力・猥褻・恋愛・猟奇的・政治的・宗教的表現を含む（R-15相当以上）作品への利用』

　　　・必ず元々のモデル等の規約範囲をご確認の上、ご利用ください
　　　・また作品を公開される際には、検索避け等のご配慮をよろしくお願いいたします

　　※『営利目的の利用』は本ツールにおいては禁止事項ではありませんが、PMXEditorでは禁止事項に当たるためご注意ください

　《免責事項》

　　・自己責任でご利用ください
　　・ツール使用によって生じたいかなる問題に関して、作者は一切の責任を負いかねます


----------------------------------------------------------------
■　ソースコード・ライブラリ
----------------------------------------------------------------

このツールは、pythonで作成しており、以下ライブラリを使用・同梱しています。

・numpy (https://pypi.org/project/numpy/)
・bezier (https://pypi.org/project/bezier/)
・numpy-quaternion (https://pypi.org/project/numpy-quaternion/)
・wxPython (https://pypi.org/project/wxPython/)
・pyinstaller (https://pypi.org/project/PyInstaller/)

ソースコードは、Githubで公開しています。(MITライセンス)
ただし、著作権は放棄しておりません。

https://github.com/miu200521358/pmx_dressup

ツールアイコンは、icon-rainbow様よりお借りしています
https://icon-rainbow.com/%E3%83%AF%E3%83%B3%E3%83%94%E3%83%BC%E3%82%B9%E3%81%AE%E7%84%A1%E6%96%99%E3%82%A2%E3%82%A4%E3%82%B3%E3%83%B3%E7%B4%A0%E6%9D%90-2/

ツール内のアイコンは、Google Material Icon様よりお借りしています。
https://fonts.google.com/icons


----------------------------------------------------------------
■　クレジット
----------------------------------------------------------------

　ツール名： PmxDressup
　作者：　miu もしくは miu200521358

　http://www.nicovideo.jp/user/2776342
　Twitter: @miu200521358
　Mail: garnet200521358@gmail.com


----------------------------------------------------------------
■　履歴
----------------------------------------------------------------

PmxDressup_1.00.02 (2023/10/22)
■ バグ修正
 - IKリンクボーンが出力されており、かつIKボーンが出力されない場合があったのを修正
 - お着替えモデル出力時のパス整合性判定がまだ作っていないフォルダの存在チェックをしていたので削除
 - 腕系ボーンの移動オフセット判定時に肩Cがない場合にエラーになる場合があったのを修正
 - 首と頭の回転フィッティングを削除
 - 体幹の移動Xと回転YZを無視するよう処理追加
 - 子ボーンが出力対象である場合、親ボーンを出力するよう修正
 - ボーンが紐付いていない剛体を出力するよう修正

PmxDressup_1.00.01 (2023/09/22)
■ 機能追加・改修
 - 猫耳などパーツでのお着替えもできるよう調整
 - SDEFパラメーター再計算処理追加
 - 袖IKなどの準標準外フィッティングを調整
 - 靴の大きさを人物と衣装の靴底（Z方向の幅）の比率で決めるよう処理修正
 - 上半身3を準標準チェック対象に追加
 - 握り拡散系は出力しないようスキップ処理追加
■ バグ修正
 - 衣装のモーフが表示枠に入らない場合があったのを修正
 - 全ての親がないPMXモデルも付けられるよう修正
 - 足首などグローバルで個別調整する場合にY回転が左右同一の回転ではなかったのを修正
 - 上半身や下半身などのボーン位置調整を行う際の基準ボーンから頭・首を除外
 - お着替えモデル出力時にIKボーンの出力判定が間違っていたので修正
 - PMXモデル名にファイル出力出来ない文字が入っていた場合に除去するように修正

PmxDressup_1.00.00 (2023/08/20)
 一般配布開始

