# ssh
## 安装
```bash
pip3 install python3-ssh
```

## 用法
### is_sshable 用于判断服务器是否可以ssh
如下所示
```python
from ssh.ssh import SSHClient


if __name__ == '__main__':
    ssh = SSHClient(ip="192.168.1.2", port=22, username="root", password="xxxx")
    print(ssh.is_sshable)
```

执行结果：
```bash
True
```
其中在建立ssh连接时，默认超时时间为10秒，通常情况下，10超时时间是够了的，但当网络环境确实很差而且无法优化网络环境的情况下，也可以设置连接超时的，如下即将超时时间修改为30秒
```python
from ssh.ssh import SSHClient


if __name__ == '__main__':
    ssh = SSHClient(ip="192.168.1.2", port=22, username="root", password="xxxx",connect_timeout=30)
    print(ssh.is_sshable)
```
### wait_for_sshable 设置超时等待服务器可以ssh
* 对于新建的虚拟机，可以使用等待可以ssh，并可以设置超时，如下示例中 192.168.1.254 为一个不存在的虚拟机
```python
from ssh.ssh import SSHClient


if __name__ == '__main__':
    ssh = SSHClient(ip="192.168.1.2", port=22, username="root", password="Mugen_runner@123456")
    rs=ssh.wait_for_sshable(60)
    print(rs)
    ssh = SSHClient(ip="192.168.1.254", port=22, username="root", password="Mugen_runner@123456")
    rs = ssh.wait_for_sshable(60)
    print(rs)
```
执行结果为：
```bash
True
False
```
### exec 用于执行命令
* 执行一条简单的命令，并获取执行命令的返回码、标准输出和标准错误
远程执行一条简单的命令，比如 ls，调试时需要将ip地址和用户名密码修改为自己的调试环境的信息
```python
from ssh.ssh import SSHClient


if __name__ == '__main__':
    ssh = SSHClient(ip="192.168.1.2", port=22, username="root", password="xxxx")
    rs = ssh.exec("ls /")
    print(f"exit_status_code:{rs.exit_status_code}")
    print(f"stdout:{rs.stdout}")
    print(f"stderr:{rs.stderr}")
```
执行结果如下：
```bash
exit_status_code:0
stdout:afs
bin
boot
dev
etc
home
lib
lib64
lost+found
media
mnt
opt
proc
root
run
sbin
srv
sys
tmp
usr
var

stderr:
```

