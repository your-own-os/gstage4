# gstage4
A python module for buildling stage4 of Gentoo Linux



TODO:
linux-6.15: CONFIG_NULL_TTY_DEFAULT_CONSOLE

I was able to build libreoffice on gentoo without the X11 libs using --without-x and --disable-randr, however when running,  I get "no suitable windowing system found, exiting.


如果不使用 utmpx/wtmp 相关功能，以下是通常可以禁用（mask）的主要执行文件及其所属安装包（基于 Debian/Ubuntu 系统，其他发行版可能略有差异）：
可禁用的执行文件	所属安装包	功能说明
/usr/bin/w	procps	显示当前登录用户及其活动（依赖 utmpx）
/usr/bin/who	coreutils	显示当前登录用户列表（依赖 utmpx）
/usr/bin/last	util-linux	显示历史登录记录（依赖 wtmp）
/usr/bin/lastb	util-linux	显示失败的登录尝试记录（依赖 btmp，wtmp 的姊妹文件）
/usr/bin/lastlog	shadow-utils	显示用户最后一次登录时间（依赖 lastlog 文件，与 wtmp 机制类似）
/usr/sbin/accton	acct	启用 / 禁用进程记账（部分系统中与登录记录关联）
/usr/bin/users	coreutils	显示当前登录的用户名称（依赖 utmpx）
/usr/bin/idle	util-linux	显示用户空闲时间（部分系统中依赖登录记录）

部分系统监控工具（如 monit、nagios）可能依赖 w/who 判断用户登录状态，禁用前需确认业务是否依赖。
pam_lastlog 等 PAM 模块可能会尝试更新 lastlog，禁用后可能产生无关错误日志（可通过 PAM 配置屏蔽）。
