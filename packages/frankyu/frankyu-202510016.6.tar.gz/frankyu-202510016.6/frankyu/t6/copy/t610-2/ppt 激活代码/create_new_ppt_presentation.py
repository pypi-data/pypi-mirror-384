import  frankyu.pptx.create_new_ppt_presentationD as cr

def create_new_ppt_presentation(path=r"https://d.docs.live.net/9122e41a29eea899/sb_yufengguang/ppt"):
    

    a,pp,c=cr.create_new_ppt_presentationD(kill_existing_ppt=0)
    
    pp.SaveAs("//".join([path,pp.Name+".pptx"]))
    print("已经保存到","//".join([r"https://d.docs.live.net/9122e41a29eea899/sb_yufengguang/ppt"," "]))

if __name__ == "__main__":
    create_new_ppt_presentation(path=r"https://d.docs.live.net/9122e41a29eea899/sb_yufengguang/ppt")
    

