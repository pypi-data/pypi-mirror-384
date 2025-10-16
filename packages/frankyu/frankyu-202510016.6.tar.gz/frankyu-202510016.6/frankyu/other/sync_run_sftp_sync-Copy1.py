import os
import sys
import logging
import ftpsync.targets
import ftpsync.sftp_target
from ftpsync.synchronizers import BiDirSynchronizer
from ftpsync.util import CliSilentRuntimeError



aaa = r'''


SFTP 連線參數
ssh_host (str)

預設值: "192.168.95.216"

說明: 這是您 SFTP 伺服器的網路位址。它可以是一個 IP 地址（例如上面所示的內網 IP），也可以是一個域名（例如 "ftp.example.com"）。確保這個地址是正確且可從執行腳本的機器訪問的。

ssh_username (str)

預設值: "u0_a454"

說明: 這是用於登入 SFTP 伺服器的使用者名稱。SFTP 伺服器會使用這個使用者名稱來驗證您的身份。

ssh_password (str)

預設值: "Liteon@2022"

說明: 這是與 ssh_username 匹配的密碼。請確保這個密碼是正確的，因為錯誤的密碼會導致認證失敗。注意：在腳本中直接硬編碼密碼並不安全，在生產環境中建議使用環境變數、金鑰檔或更安全的憑證管理方式。

ssh_port (int)

預設值: 8022

說明: 這是 SFTP 伺服器監聽連線的埠號。SFTP 的預設埠是 22，但您的配置顯示是 8022，這通常表示 SFTP 服務運行在一個非標準埠上。

本地與遠端資料夾路徑
local_dir_linux (str)

預設值: "/home/frank/360a/t7_py/"

說明: 當腳本在 Linux 或 macOS 系統上執行時，將以此路徑作為本地同步的根資料夾。它應該是您的本地文件系統中實際存在的路徑。

local_dir_windows (str)

預設值: "N:/OneDrive/私人文件，dengchunying1988/Documents/sb_py/"

說明: 當腳本在 Windows 系統上執行時，將以此路徑作為本地同步的根資料夾。它也應該是您本地文件系統中實際存在的路徑。腳本會根據 sys.platform 自動判斷使用哪個本地路徑。

remote_dir (str)

預設值: "/storage/emulated/0/Download/360a/t7_py/"

說明: 這是 SFTP 伺服器上用於同步的遠端資料夾路徑。請確保您提供的路徑在 SFTP 伺服器上是正確的，且 SFTP 使用者有權限讀取和寫入該目錄。

日誌與同步行為參數
log_level (int)

預設值: logging.INFO

說明: 設定 Python 日誌模組的輸出詳細程度。

logging.DEBUG (10): 輸出所有詳細的偵錯信息。

logging.INFO (20): 輸出一般信息，指示程式的進度。

logging.WARNING (30): 輸出潛在的問題或非關鍵錯誤。

logging.ERROR (40): 輸出程式執行中遇到的錯誤。

logging.CRITICAL (50): 輸出嚴重錯誤，可能導致程式終止。

sync_mode (str)

預設值: "sync"

說明: 定義同步的方向和行為。

"sync" (雙向同步): 比較本地和遠端檔案，並根據時間戳和內容差異來同步兩邊，確保兩邊的檔案狀態一致。

"upload" (上傳): 只將本地的更改上傳到遠端伺服器。

"download" (下載): 只將遠端的更改下載到本地。

sync_verbose (int)

預設值: 5

說明: 控制 pyftpsync 庫自身的詳細日誌輸出級別，與 log_level 不同，它影響 pyftpsync 內部顯示的同步進度信息。範圍通常是 0 (最少) 到 5 (最詳細)。

sync_dry_run (bool)

預設值: False

說明: 如果設定為 True，同步操作將只會模擬執行，而不會對實際文件進行任何修改。這對於在實際執行同步前預覽將發生的變更非常有用。設定為 False 才會真正執行同步。

sync_delete (bool)

預設值: False

說明: 如果設定為 True，同步器將會刪除在其中一端不存在但在另一端存在的文件。例如，如果本地刪除了某個文件，遠端也會被刪除；反之亦然。請謹慎使用此選項，因為它可能導致數據丟失。

sync_force (bool)

預設值: False

說明: 如果設定為 True，同步器將會強制覆蓋目標文件，而不檢查文件的時間戳或內容是否最新。這可能會導致較新版本的檔案被較舊版本覆蓋。

sync_resolve (str)

預設值: "remote"

說明: 定義當本地和遠端文件都發生修改時如何處理衝突。

"local": 以本地檔案的版本為準，覆蓋遠端檔案。

"remote": 以遠端檔案的版本為準，覆蓋本地檔案。

"ask": 當發生衝突時，提示使用者手動決定如何解決。

"skip": 跳過任何有衝突的檔案，不進行同步。

sync_ignore_passive_ip (bool)

預設值: True

說明: 這是一個與 FTP 協議相關的選項。某些網絡配置下，FTP 伺服器在被動模式下報告的 IP 地址可能無法從客戶端訪問。設定為 True 可以忽略伺服器報告的被動模式 IP，嘗試直接連接。對於 SFTP（SSH File Transfer Protocol），這個參數通常不適用，因為 SFTP 不使用被動模式。但作為通用同步庫的選項，它可能仍然存在。

sync_no_verify_host_keys (bool)

預設值: True

說明: 如果設定為 True，SFTP 連線將不會驗證伺服器的主機金鑰。在首次連接到新的 SFTP 伺服器時，通常會提示您驗證其主機金鑰。為了安全起見，在生產環境中不建議將此選項設定為 True，因為它會讓您容易受到中間人攻擊。 通常只在內部或測試環境中使用。

sync_exclude (str)

預設值: ".DS_Store,.git,.hg,.svn,#recycle,frankyu/frankyu/t7/t7042/"

說明: 這是以逗號分隔的模式字串，用於指定在同步過程中應排除的文件或資料夾。這些模式使用 fnmatch 風格的通配符（例如 * 和 ?）。此參數在 sync_match 之後應用，所以如果一個文件既匹配又排除，它將被排除。

sync_match (str)

預設值: *.py

說明: 這是以逗號分隔的模式字串，用於指定在同步過程中只應包含的文件名。這些模式也使用 fnmatch 風格的通配符。例如，"*.py" 表示只同步所有 .py 結尾的文件。如果未指定，則預設匹配所有文件。

'''



# --- 配置日誌記錄 (在函數外部配置，以便在函數呼叫前就生效) ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_sftp_sync(
    ssh_host: str = "192.168.34.137",
    ssh_username: str = "u0_a454",
    ssh_password: str = "Liteon@2022",
    ssh_port: int = 8022,
    local_dir_linux: str = "/home/frank/360a/t7_py/",
    local_dir_windows: str = "N:/OneDrive/私人文件，dengchunying1988/Documents/sb_py/",
    remote_dir: str = "/storage/emulated/0/Download/360a/t7_py/",
    log_level: int = logging.INFO, # 可以在這裡調整日誌級別，但basicConfig已在外部設定
    sync_mode: str = "sync",
    sync_verbose: int = 5,
    sync_dry_run: bool = False,
    sync_delete: bool = False,
    sync_force: bool = False,
    sync_resolve: str = "remote",
    sync_ignore_passive_ip: bool = True,
    sync_no_verify_host_keys: bool = True,
    sync_exclude: str = ".DS_Store,.git,.hg,.svn,#recycle,frankyu/frankyu/t7/t7042/",
    sync_match: str = "*.py"
):
    """
    執行本地資料夾與 SFTP 伺服器的同步。

    參數:
        ssh_host (str): SFTP 伺服器的主機 IP 地址或域名。
        ssh_username (str): 用於 SFTP 連線的使用者名稱。
        ssh_password (str): 用於 SFTP 連線的密碼。
        ssh_port (int): SFTP 伺服器的埠號。
        local_dir_linux (str): Linux 系統下的本地資料夾路徑。
        local_dir_windows (str): Windows 系統下的本地資料夾路徑。
        remote_dir (str): 遠端 SFTP 伺服器上的資料夾路徑。
        log_level (int): 設置日誌記錄級別 (例如: logging.INFO, logging.DEBUG)。
        sync_mode (str): 同步模式 ('sync', 'upload', 'download')。
        sync_verbose (int): 日誌詳細程度 (0-5, 5最詳細)。
        sync_dry_run (bool): 是否執行模擬運行而不實際修改文件。
        sync_delete (bool): 是否刪除遠端或本地不存在的文件。
        sync_force (bool): 是否強制覆蓋，不檢查時間戳。
        sync_resolve (str): 衝突解決策略 ('local', 'remote', 'ask', 'skip')。
        sync_ignore_passive_ip (bool): 是否忽略被動模式下的 IP 地址。
        sync_no_verify_host_keys (bool): 是否忽略主機金鑰驗證。
        sync_exclude (str): 以逗號分隔的排除模式字串（檔案和資料夾）。
        sync_match (str): 以逗號分隔的匹配模式字串（只適用於檔案）。
    """

    # 設置日誌級別 (如果需要動態調整，可以在這裡重新配置)
    logging.getLogger().setLevel(log_level)

    # 根據作業系統確定本地路徑
    if sys.platform.startswith('win'):
        logging.info("檢測到 Windows 平台。")
        local_path = os.path.normpath(os.path.expandvars(local_dir_windows))
    elif sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
        logging.info("檢測到 Linux 或 macOS 平台。")
        local_path = os.path.normpath(os.path.expanduser(local_dir_linux))
    else:
        logging.warning(f"未知作業系統平台: {sys.platform}。使用默認 Windows 路徑。")
        local_path = os.path.normpath(os.path.expandvars(local_dir_windows))
    
    sftp_url_display = f"sftp://{ssh_username}@{ssh_host}:{ssh_port}{remote_dir}" 
    
    logging.info(f"本地同步路徑: {local_path}")
    logging.info(f"遠端 SFTP 同步路徑: {sftp_url_display}")

    # --- 前置檢查 ---
    if not os.path.exists(local_path):
        logging.error(f"錯誤: 本地資料夾 '{local_path}' 不存在。請創建它或檢查路徑。")
        sys.exit(1)
    if not os.access(local_path, os.R_OK | os.W_OK):
        logging.error(f"錯誤: 對本地資料夾 '{local_path}' 沒有讀取或寫入權限。請檢查權限設定。")
        sys.exit(1)

    local_target = None
    sftp_target = None

    try:
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

        # --- 設置同步選項 ---
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
        
        logging.info("資料夾同步完成！")
        logging.info(f"同步結果摘要: {result}")
        if result.get('errors'):
            logging.warning(f"同步過程中出現警告/錯誤: {result['errors']}")

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
        if local_target and local_target.connected:
            local_target.close()
        if sftp_target and sftp_target.connected:
            sftp_target.close()

if __name__ == "__main__":
    # 您可以直接呼叫函數，所有參數都會使用預設值
    #run_sftp_sync()

    # 或者，您可以傳遞自定義參數來覆寫預設值
    run_sftp_sync(
        ssh_host="192.168.34.137",
        ssh_username="u0_a454",
        ssh_password="Liteon@2022",
        ssh_port = 8022,
        local_dir_linux = "/home/frank/360a/t7_py/",
        local_dir_windows = "N:/OneDrive/私人文件，dengchunying1988/Documents/sb_py/",
        remote_dir = "/storage/emulated/0/Download/360a/t7_py/",
        #sync_mode= "sync",
        #sync_mode= "download",
        sync_mode= "upload",
        #sync_match = "*.py",
        sync_match = 0,
        sync_dry_run = False,
        sync_verbose=5,
        
        #sync_dry_run=True, # 執行一次模擬運行
        sync_exclude="*.log,temp_folder/", # 排除日誌檔案和特定資料夾
        #log_level=logging.DEBUG ,# 設定為DEBUG級別以獲取更詳細日誌
        log_level=logging.INFO
        
        
        
     )



