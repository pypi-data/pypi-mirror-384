#!/usr/bin/env python
# coding: utf-8

# In[9]:


def xinJianBook():
    import frankyu.excel as ex
    app =   ex.initialize_excel()
    ex.create_workbook(app)
#xiJianBook()



    

    import frankyu.excel as ex
    app =   ex.initialize_excel()
    ex.create_workbook(app)
# In[38]:


#ap = xlwings.apps
def excelpid():
    import xlwings
    bbb = []
    for i in xlwings.apps:
        bbb.append(i.pid)
        #print(i.pid)
    #print(bbb)
    
    if len(bbb)>=(1):
        #print(789)

        #print(bbb)
        return bbb[0]
    else:        

        
        #print(123)
        xinJianBook()
        

        import xlwings
        bbb = []
        for i in xlwings.apps:
            bbb.append(i.pid)
            print(i.pid)
        #print(bbb)
        return bbb[0]
    


# In[66]:


def xieRuBiaoGe(timeWait = 4):

    excelpid()

    
   
    
    import xlwings
    rng = xlwings.apps[excelpid()].books[0].sheets[0].range("A1")
    rng.value = "=2+454645657567657567"
    sheet = rng.sheet
    book = sheet.book
    app = book.app
    import frankyu.excel as exc
    import datetime
    path = str(datetime.datetime.now()).replace(":"," ").replace("-"," ").replace("."," ").replace(":"," ").replace(":"," ").replace(":"," ").replace(":"," ").replace(" ","")
    import os
    
    path2 = "".join([os.getcwd(),"\\",path,".xlsx"])
    
    book.save(path2)
    import time
    time.sleep(timeWait)
    app.quit()
#xieRuBiaoGe(3)


# In[68]:


#xieRuBiaoGe(1)


# In[ ]:




