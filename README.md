# gstage4
A python module for buildling stage4 of Gentoo Linux



TODO:

I was able to build libreoffice on gentoo without the X11 libs using --without-x and --disable-randr, however when running,  I get "no suitable windowing system found, exiting.


以 shadow-utils 中的 login 为例（主流 Linux 发行版常用）
shadow-utils 是提供 login、passwd 等工具的基础包，其 login 程序支持通过编译选项控制是否生成 utmp/wtmp 记录。
相关编译选项：
--disable-utmp
禁用 login 对 utmp（当前登录记录）的写入操作。
--disable-wtmp
禁用 login 对 wtmp（历史登录记录）的写入操作。
--disable-lastlog
禁用对 lastlog 文件（用户最后登录时间）的更新（与 wtmp 机制类似）。