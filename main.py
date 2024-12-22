from fastapi import FastAPI, File
from fastapi import UploadFile
import uvicorn
import pandas as pd
import pdfplumber
from fastapi.encoders import jsonable_encoder


app=FastAPI()


def Data_processing(page_words:tuple):
    """processes the table dta and returns table values"""
    table_values,column_values=page_words[0],page_words[1]
    required_values=[]
    extra_values=[]
    n=0
    for _ in range(n,len(table_values)):
        if n<len(table_values):
            val_top=table_values[n]['top']
            val_bottom=table_values[n]['bottom']
            temp=[x for x in table_values if x['top']<val_bottom and x['bottom']>val_top]
            l=len(column_values)
            if len(temp)>l//2:
                for i in column_values:
                    if column_values[-1]['text']==i['text'] and n==len(table_values):
                        required_values.append('')
                    for _  in range(n,len(table_values)):
                        if table_values[n]['x0']<i['x1'] and table_values[n]['top']<val_bottom and table_values[n]['bottom']>val_top:
                            required_values.append(table_values[n]['text'])
                            n+=1
                            break
                        else:
                            required_values.append('')
                            break
            else:
                extra_values.extend(temp)
                n+=1
        else:
            break
    return required_values,extra_values



def line_breaker(word:dict,all_lines:dict,req_page:list):
    """gives table breaking value"""
    for page in all_lines:
        if req_page==page:
            lines=[line for line in all_lines[page][0] if line['top']>word['bottom']]
            if len(lines)==1:
                return -1
            else:
                return lines[1]
    return 0
            


def find_header(header_name:str,all_words:dict,all_lines:dict):
        """finds the header match in each page and returns table_words"""
        a=[]
        for page in all_words:
            page_words=all_words[page]
            for words in page_words:
                for word in words:
                    if header_name.lower() == word["text"].lower().split(":")[0]:
                        column_values=[column for column in words if abs(column['top']-word['bottom'])<10]
                        line_break=line_breaker(word,all_lines,page)
                        if line_break==-1:
                            end=words[-1]['top']
                        else:
                            end=line_break['top']
                        table_words=[x for x in words if x['top']>column_values[0]['bottom'] and x['top']<end ]
                        a.append((table_words,column_values))
        return a


def data_sorting(required_values:list,extra_values:list,column_values:list,header:str):
    """sorts table data w.r.t to columns"""
    page_dict={}
    for n,i in enumerate(column_values):
        page_dict[i['text']]=[]
        v=n
        value=[]
        for _ in required_values:
            if v< len(required_values):
                value.append(required_values[v])
                v+=len(column_values)
        page_dict[i['text']]=value
    page_df1=pd.DataFrame(page_dict)
    page_df1.rename(columns = {'Item':f'{header}_Item'},inplace=True)

    if len(extra_values)>=len(column_values):
        extra_names=[x['text'].split(':')[0] for x in extra_values]
        extra_heads=list(set(extra_names))
        dict1={}
        for i in extra_heads:
            dict1[i]=[]
            values=[x['text'].split(":")[-1] for x in extra_values if x['text'].split(":")[0] in i]
            dict1[i]=values
        page_df2=pd.DataFrame(dict1)
        
        page_df=pd.concat([page_df1,page_df2],axis=1)
    else:
        page_df=page_df1

    return page_df

def extract_all_words(pdf:object):
    """extracts all_words from pdf"""
    all_words={}
    for page in pdf.pages:
        all_words[page]=[]
        all_words[page]=[page.extract_words(keep_blank_chars=True,x_tolerance=1,y_tolerance=1)]
    return all_words

def lines_extractor(pdf:object):
    """extracts all_lines from pdf"""
    all_lines={}
    for page in pdf.pages:
        all_lines[page]=[]
        all_lines[page]=[page.lines]
    return all_lines


@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI app!"}




def my(file_path):
    try:
        file_path=r"C:\Users\manan\OneDrive\Desktop\Python\Purchase\Purchase Order 6000521638 _ SLI.PDF"
        """It's main func, takes file_path as input and extracts tables if found"""
        all_dfs=[]
        header_names=['component details','release details','details']
        pdf=pdfplumber.open(file_path)
        all_Words=extract_all_words(pdf)
        all_lines=lines_extractor(pdf)
        for header in  header_names:
            table_words=find_header(header,all_Words,all_lines)
            if len(table_words)!=0:
                page_dfs=[]
                for page_words in table_words:
                    data=Data_processing(page_words)
                    df=data_sorting(data[0],data[1],page_words[1],header)
                    page_dfs.append(df)
                final_df=pd.concat(page_dfs)
                all_dfs.append(final_df)
                print(f"table extracted with header_name:'{header}'")

            else:
                print(f"data not found with header_name: '{header}'")
        final= pd.concat(all_dfs,axis=1)
        return final
    except Exception as e:
        return {"error": str(e)}
    

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    a=jsonable_encoder(my(file))
    # Do something with the file, e.g., save it or process it
    return a

if __name__== "__main__":
    uvicorn.run("main:app")