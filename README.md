# pmx_dressup

## submodule

### 追加方法

管理者権限で開いたターミナルで実行する

 1. `git submodule add -b develop https://github.com/miu200521358/mmd_base.git mmd_base`
 2. `cd C:\MMD\pmx_dressup\src`
 3. `mklink /D mlib ..\mmd_base\mlib`

### 更新方法

 1. `git submodule update --remote`