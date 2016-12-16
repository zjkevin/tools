import os
import shutil
import hashlib
from functools import cmp_to_key
from datetime import datetime
import codecs

# 1、当源目录中数据被删除时，备份目录相应的文件修改文件名后增加___DEL
# 防止误操作留下不可挽回的文件误删
# 2、源目录可以备份到多个备份文件目录
# 3、支持多种数据库，扫描记录是否存数据库可配
# 4、修改文件后，备份目录的文件不删除，保留修改前的文件加后缀___MODIF1

def file_md5(file_path):
    m = hashlib.md5()
    n = 1024*4
    with open(file_path,'rb') as f:
        while True:
            buf = f.read(n)  
            if buf:
                m.update(buf)  
            else:
                break
    return m.hexdigest()

# 源路径
source_path = r"/home/kevin"
# 备份目录支持多个
backup_path = [r"/media/kevin/Samsung USB/backup"]
log_prefix = datetime.now().strftime("%Y%m%d%H%M%S%f")
# 修改日志
mod_log = "mod_%s.log" % log_prefix 
# 删除日志
del_log = "del_%s.log" % log_prefix
# 处理日志
process_log = "%s.log" % log_prefix

MODIF_SAVE = True
DEL_SAVE = True

def check_backup_path(path):
	return os.path.exists(path)

def mod_log_write(mes):
    log_write(mes,mod_log)

def del_log_write(mes):
    log_write(mes,del_log)

def process_log_write(mes):
    log_write(mes,process_log)

def log_write(mes,path):
    path = os.path.join(os.path.abspath("."), path)
    with codecs.open(path, 'a+', 'utf-8') as f:
        f.write("%s\n" % mes)

# 源目录-> 备份目录
def back_up_process(source_path,backup_path,modif=True):
    if not check_backup_path(backup_path):
        process_log_write("back path not exist")
        exit(1)
    i = 1
    for parent,dirnames,filenames in os.walk(source_path):
        sub_dir = parent.replace(source_path,"")
        
        if sub_dir != "":
            if sub_dir[0] == "\\" or sub_dir[0] == "/":
                sub_dir = sub_dir[1:]
            if sub_dir[-1] == "\\" or sub_dir[-1] == "/":
                sub_dir = sub_dir[:-1]
        process_log_write("子目录:%s" % sub_dir)
    
        for d in dirnames:
            process_log_write("源目录:%s" % os.path.join(parent,d))
            # 检查备份目录是否有该目录 没有则新建 有则pass
            process_log_write("备份目录 %s" % os.path.join(backup_path,sub_dir,d))
            process_log_write(os.path.exists(os.path.join(backup_path,sub_dir,d)))
            if not os.path.exists(os.path.join(backup_path,sub_dir,d)):
                process_log_write("mkdir...".center(80,'-'))
                os.makedirs(os.path.join(backup_path,sub_dir,d))
        for f in filenames:
            process_log_write("源文件:%s" % os.path.join(parent,f))
            if not os.path.exists(os.path.join(backup_path,sub_dir,f)):
                process_log_write("copy...".center(80,'-'))
                shutil.copyfile(os.path.join(parent,f),os.path.join(backup_path,sub_dir,f))
            else:
                #对比文件的md5值，如果一样就pass 不一样就覆盖
                md51 = file_md5(os.path.join(parent,f))
                md52 = file_md5(os.path.join(backup_path,sub_dir,f))
                if md51 == md52:
                    process_log_write("文件一样")
                else:
                    process_log_write("文件不一样")
                    # 将文件重名为 文件名+_modif+修改编号 此处可配置，如果设置为0 则直接覆盖，
                    # 如果设置为1 则会最多保留最近的一次修改文件
                    # 如果设置为n 则会保留最近的n次修改
                    if os.path.isfile(os.path.join(backup_path,sub_dir,f)):
                        if modif:
                            # 修改文件名
                            modif_index = 0
                            modif_file_list = []
                            ismodif = False
                            while modif_index < 9:
                                modif_index = modif_index + 1
                                modif_file_path = os.path.join(backup_path,sub_dir,f+"_%s___MODIF" % modif_index)
                                if os.path.exists(modif_file_path):
                                    #print(os.path.getctime("%s%s" % (os.path.join(backup_path,sub_dir,f+"___MODIF"),modif_index)))
                                    modif_file_list.append({"modif_id":modif_index,"modif_file_path":modif_file_path,"modif_time":
                                        os.path.getmtime(modif_file_path)})
                                    continue
                                else:
                                    mod_log_write(modif_file_path)
                                    os.rename(os.path.join(backup_path,sub_dir,f),modif_file_path)
                                    ismodif = True
                                    break
                            if not ismodif:
                                modif_file_list.sort(key=cmp_to_key(lambda x,y: x['modif_time']-y['modif_time']),reverse=False)
                                process_log_write("删除:%s" % modif_file_list[0]['modif_file_path'])
                                os.remove(modif_file_list[0]['modif_file_path'])
                                os.rename(os.path.join(backup_path,sub_dir,f),modif_file_list[0]['modif_file_path'])
                        else:
                            os.remove(os.path.join(backup_path,sub_dir,f))
                    shutil.copyfile(os.path.join(parent,f),os.path.join(backup_path,sub_dir,f))    

        process_log_write("循环index:%s" % i)
        i = i + 1

# 备份目录->源目录
# 检查被删除的目录或者文件夹，删除的做标记
def del_check_process(backup_path,source_path,del_check=True):
    if not check_backup_path(backup_path):
        process_log_write("back path not exist")
        exit(1)
    i = 1
    for parent,dirnames,filenames in os.walk(backup_path):
        sub_dir = parent.replace(backup_path,"")
        if sub_dir != "":
            if sub_dir[0] == "\\" or sub_dir[0] == "/":
                sub_dir = sub_dir[1:]
            if sub_dir[-1] == "\\" or sub_dir[-1] == "/":
                sub_dir = sub_dir[:-1]
        process_log_write("子目录:%s" % sub_dir)
    
        for d in dirnames:
            # 忽略已经更名为删除标记的目录 ___DEL结尾
            if len(d) > 6 and d[-6:] == "___DEL":
                continue
            process_log_write("备份目录:%s" % os.path.join(parent,d))
            # 检查备份目录是否有该目录 没有则新建 有则pass
            process_log_write("源目录 %s" % os.path.join(source_path,sub_dir,d))
            # 源目录已经删除
            if not os.path.exists(os.path.join(source_path,sub_dir,d)):
                # 备份目录更名
                if del_check:
                    del_log_write(os.path.join(backup_path,sub_dir,d+"___DEL"))
                    os.rename(os.path.join(backup_path,sub_dir,d),os.path.join(backup_path,sub_dir,d+"___DEL"))
                else:
                    # 直接删除
                    shutil.rmtree(os.path.join(backup_path,sub_dir,d))
        for f in filenames:
            process_log_write("备份文件:%s" % os.path.join(parent,f))
            # 忽略已经修改为删除的文件
            if len(f) > 6 and f[-6:] == "___DEL" or f[-5:] == "MODIF" :
                continue
            if not os.path.exists(os.path.join(source_path,sub_dir,f)):
                # 源文件已经删除 修改为___DEL结尾
                if del_check:
                    del_log_write(os.path.join(parent,f+"___DEL"))
                    os.rename(os.path.join(parent,f),os.path.join(parent,f+"___DEL"))
                else:
                    # 直接删除 
                    os.remove(os.path.join(parent,f))
        print("循环index:%s" % i)
        i = i + 1

# 清空删除文件
# 如果datetime为空，则清楚所有文件
# 清除datetime时间之前的所有文件
def clear_del_files(path,datetime=None):
    pass

def clear_modif_files(path,datetime=None):
    pass


if __name__ == "__main__":

    
    for b_p in backup_path:
        back_up_process(source_path,b_p,MODIF_SAVE)

    for b_p in backup_path:
        del_check_process(b_p,source_path,DEL_SAVE)




