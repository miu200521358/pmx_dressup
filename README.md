# pmx_dressup

## submodule

### 追加方法

管理者権限で開いたターミナルで実行する

 1. `git submodule add -b develop https://github.com/miu200521358/mmd_base.git mmd_base`
 2. `mkdir src`
 3. `cd src`
 4. `mklink /D mlib ..\mmd_base\mlib`

### 更新方法

 1. `git pull`
 1. `git submodule update --remote`

### アプリアイコン

 https://icon-rainbow.com/%E3%83%AF%E3%83%B3%E3%83%94%E3%83%BC%E3%82%B9%E3%81%AE%E7%84%A1%E6%96%99%E3%82%A2%E3%82%A4%E3%82%B3%E3%83%B3%E7%B4%A0%E6%9D%90-2/

### 翻訳

 1. potファイルを作成
    - `pybabel extract -o src/i18n/messages.pot .`
 1. poファイルを言語別に作成
    - `pybabel init -i src/i18n/messages.pot -l ja -d ja -o src/i18n/ja/messages.po`
    - `pybabel init -i src/i18n/messages.pot -l en -d en -o src/i18n/en-us/messages.po`
    - `pybabel init -i src/i18n/messages.pot -l zh -d zh -o src/i18n/zh/messages.po`
    - `pybabel init -i src/i18n/messages.pot -l ko -d ko -o src/i18n/ko/messages.po`
 1. translate.batを実行