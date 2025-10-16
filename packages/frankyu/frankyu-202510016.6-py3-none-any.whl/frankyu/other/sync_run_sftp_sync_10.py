import os
import sys
import logging
import ftpsync.targets
import ftpsync.sftp_target
from ftpsync.synchronizers import BiDirSynchronizer
from ftpsync.util import CliSilentRuntimeError
import paramiko

# --- 配置日誌記錄 (在函數外部配置，以便在函數呼叫前就生效) ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def ensure_remote_dir(ssh_host, ssh_port, ssh_username, ssh_password, remote_dir):
    """
    使用 paramiko 遞歸創建遠端 SFTP 目錄（如果不存在）。
    """
    transport = paramiko.Transport((ssh_host, ssh_port))
    transport.connect(username=ssh_username, password=ssh_password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    dirs = remote_dir.strip('/').split('/')
    cur_path = ''
    for d in dirs:
        cur_path += '/' + d
        try:
            sftp.stat(cur_path)
        except FileNotFoundError:
            try:
                sftp.mkdir(cur_path)
                logging.info(f"已創建遠端目錄: {cur_path}")
            except Exception as e:
                logging.error(f"創建遠端目錄失敗: {cur_path}，錯誤: {e}")
                raise
    sftp.close()
    transport.close()

def ensure_local_dir(local_path):
    """
    檢查本地目錄是否存在，不存在則自動創建。
    """
    if not os.path.exists(local_path):
        try:
            os.makedirs(local_path)
            logging.info(f"本地資料夾不存在，已自動創建: {local_path}")
        except Exception as e:
            logging.error(f"創建本地資料夾失敗: {local_path}，錯誤: {e}")
            sys.exit(1)
    if not os.access(local_path, os.R_OK | os.W_OK):
        logging.error(f"錯誤: 對本地資料夾 '{local_path}' 沒有讀取或寫入權限。請檢查權限設定。")
        sys.exit(1)

def run_sftp_sync(
    ssh_host="192.168.85.222",
    ssh_username="u0_a454",
    ssh_password="Liteon@2022",
    ssh_port=8022,
    path="t7/t716/send_system_info_email/",
    local_dir_linux="/home/frank/360a/t7_py/",
    local_dir_windows="N:/OneDrive/私人文件，dengchunying1988/Documents/sb_py/",
    remote_dir="/storage/emulated/0/Download/360a/t7_py/",
    log_level=logging.INFO,
    sync_mode="sync",
    sync_verbose=5,
    sync_dry_run=False,
    sync_delete=False,
    sync_force=False,
    sync_resolve="remote",
    sync_ignore_passive_ip=True,
    sync_no_verify_host_keys=True,
    sync_exclude=".DS_Store,.git,.hg,.svn,#recycle,frankyu/frankyu/t7/t7042/",
    sync_match="*.py"
):
    """
    執行本地資料夾與 SFTP 伺服器的同步。
    所有參數均有預設值。
    """
    logging.getLogger().setLevel(log_level)
    aaa = remote_dir
    remote_dir = f"{aaa}{path}"

    # 根據作業系統確定本地路徑
    if sys.platform.startswith('win'):
        local_path = os.path.normpath(os.path.expandvars(os.path.join(local_dir_windows, path)))
        logging.info("檢測到 Windows 平台。")
    elif sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
        local_path = os.path.normpath(os.path.expanduser(os.path.join(local_dir_linux, path)))
        logging.info("檢測到 Linux 或 macOS 平台。")
    else:
        local_path = os.path.normpath(os.path.expandvars(os.path.join(local_dir_windows, path)))
        logging.warning(f"未知作業系統平台: {sys.platform}。使用默認 Windows 路徑。")
    
    sftp_url_display = f"sftp://{ssh_username}@{ssh_host}:{ssh_port}{remote_dir}" 
    logging.info(f"本地同步路徑: {local_path}")
    logging.info(f"遠端 SFTP 同步路徑: {sftp_url_display}")

    # 本地路徑檢查與創建
    ensure_local_dir(local_path)

    local_target = None
    sftp_target = None

    try:
        # 先確保遠端目錄存在，否則自動創建
        ensure_remote_dir(ssh_host, ssh_port, ssh_username, ssh_password, remote_dir)
        local_target = ftpsync.targets.FsTarget(local_path)
        logging.info("本地目標創建成功。")
        sftp_target = ftpsync.sftp_target.SFTPTarget(
            path=remote_dir,
            host=ssh_host,
            port=ssh_port,
            username=ssh_username,
            password=ssh_password,
        )
        logging.info("遠端 SFTP 目標創建成功。")
        sync_options = {
            "mode": sync_mode,
            "verbose": sync_verbose,
            "dry_run": sync_dry_run,
            "delete": sync_delete,
            "force": sync_force,
            "resolve": sync_resolve,
            "ignore_passive_ip": sync_ignore_passive_ip,
            "no_verify_host_keys": sync_no_verify_host_keys,
            "exclude": sync_exclude,
            "match": sync_match,
        }
        sync = BiDirSynchronizer(local_target, sftp_target, sync_options)
        logging.info("開始執行資料夾同步...")
        result = sync.run()
        if result is True:
            logging.info("資料夾同步完成！")
        else:
            logging.warning("同步過程中出現錯誤或未完成。")
    except CliSilentRuntimeError as e:
        logging.error(f"同步失敗：一個靜默運行時錯誤發生。錯誤訊息: {e}")
        sys.exit(1)
    except Exception as e:
        error_message = str(e).lower()
        if "authentication failed" in error_message or "permission denied" in error_message:
            logging.error(f"同步失敗：SFTP 認證失敗。請檢查使用者名、密碼或 SSH 金鑰。錯誤訊息: {e}")
        elif "no such file or directory" in error_message and "remote" in error_message:
            logging.error(f"同步失敗：遠端 SFTP 路徑可能不正確或沒有創建目錄的權限。請確保遠端目標路徑已存在。錯誤訊息: {e}")
        elif "timed out" in error_message or "connection refused" in error_message:
            logging.error(f"同步失敗：無法連接到 SFTP 伺服器。請檢查伺服器地址、埠號或網路連接。錯誤訊息: {e}")
        else:
            logging.error(f"同步過程中發生未知錯誤: {e}", exc_info=True)
    finally:
        if local_target and getattr(local_target, "connected", False):
            local_target.close()
        if sftp_target and getattr(sftp_target, "connected", False):
            sftp_target.close()

if __name__ == "__main__":
    # 可以直接呼叫函數，所有參數都會使用預設值
    run_sftp_sync()