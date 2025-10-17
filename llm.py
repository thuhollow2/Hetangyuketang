import json
import os
import requests
import base64
import math
import time
import re
import ast
from concurrent.futures import ThreadPoolExecutor, as_completed

current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

timeout = config['llm']['timeout']
threads = config['llm']['threads']
models = config['llm']['models']

class LLMManager:
    def __init__(self):
        self.answers = []

    def _generate_oa_answer(self, folder, query, config):
        try:
            start = time.time()
            answer = generate_oa_answer(query, folder, config)
            end = time.time()
            usedTime = f"{end - start:.2f}s"
            if answer: self.answers.append({
                "name": config['name'],
                "type": config['type'],
                "model": config['model'],
                "score": config['score'],
                "usedTime": usedTime,
                "answer": answer
            })
        except:
            pass

    def _generate_cl_answer(self, folder, query, config):
        try:
            start = time.time()
            answer = generate_cl_answer(query, folder, config)
            end = time.time()
            usedTime = f"{end - start:.2f}s"
            if answer: self.answers.append({
                "name": config['name'],
                "type": config['type'],
                "model": config['model'],
                "score": config['score'],
                "usedTime": usedTime,
                "answer": answer
            })
        except:
            pass

    def _generate_gk_answer(self, folder, query, config):
        try:
            start = time.time()
            answer = generate_gk_answer(query, folder, config)
            end = time.time()
            usedTime = f"{end - start:.2f}s"
            if answer: self.answers.append({
                "name": config['name'],
                "type": config['type'],
                "model": config['model'],
                "score": config['score'],
                "usedTime": usedTime,
                "answer": answer
            })
        except:
            pass

    def _generate_gm_answer(self, folder, query, config):
        try:
            start = time.time()
            answer = generate_gm_answer(query, folder, config)
            end = time.time()
            usedTime = f"{end - start:.2f}s"
            if answer: self.answers.append({
                "name": config['name'],
                "type": config['type'],
                "model": config['model'],
                "score": config['score'],
                "usedTime": usedTime,
                "answer": answer
            })
        except:
            pass

    def _generate_cf_answer(self, folder, query, config):
        try:
            start = time.time()
            answer = generate_cf_answer(query, folder, config)
            end = time.time()
            usedTime = f"{end - start:.2f}s"
            if answer: self.answers.append({
                "name": config['name'],
                "type": config['type'],
                "model": config['model'],
                "score": config['score'],
                "usedTime": usedTime,
                "answer": answer
            })
        except:
            pass

    def _generate_ot_answer(self, folder, query, config):
        try:
            start = time.time()
            answer = generate_ot_answer(query, folder, config)
            end = time.time()
            usedTime = f"{end - start:.2f}s"
            if answer: self.answers.append({
                "name": config['name'],
                "type": config['type'],
                "model": config['model'],
                "score": config['score'],
                "usedTime": usedTime,
                "answer": answer
            })
        except:
            pass

    def _generate_px_answer(self, folder, query, config):
        try:
            start = time.time()
            answer = generate_px_answer(query, folder, config)
            end = time.time()
            usedTime = f"{end - start:.2f}s"
            if answer: self.answers.append({
                "name": config['name'],
                "type": config['type'],
                "model": config['model'],
                "score": config['score'],
                "usedTime": usedTime,
                "answer": answer
            })
        except:
            pass

    def _generate_sf_answer(self, folder, query, config):
        try:
            start = time.time()
            answer = generate_sf_answer(query, folder, config)
            end = time.time()
            usedTime = f"{end - start:.2f}s"
            if answer: self.answers.append({
                "name": config['name'],
                "type": config['type'],
                "model": config['model'],
                "score": config['score'],
                "usedTime": usedTime,
                "answer": answer
            })
        except:
            pass

    def _generate_ig_answer(self, folder, query, config):
        try:
            start = time.time()
            answer = generate_ig_answer(query, folder, config)
            end = time.time()
            usedTime = f"{end - start:.2f}s"
            if answer: self.answers.append({
                "name": config['name'],
                "type": config['type'],
                "model": config['model'],
                "score": config['score'],
                "usedTime": usedTime,
                "answer": answer
            })
        except:
            pass

    def _generate_zp_answer(self, folder, query, config):
        try:
            start = time.time()
            answer = generate_zp_answer(query, folder, config)
            end = time.time()
            usedTime = f"{end - start:.2f}s"
            if answer: self.answers.append({
                "name": config['name'],
                "type": config['type'],
                "model": config['model'],
                "score": config['score'],
                "usedTime": usedTime,
                "answer": answer
            })
        except:
            pass

    def _generate_dm_answer(self, folder, query, config):
        try:
            start = time.time()
            answer = generate_dm_answer(query, folder, config)
            end = time.time()
            usedTime = f"{end - start:.2f}s"
            if answer: self.answers.append({
                "name": config['name'],
                "type": config['type'],
                "model": config['model'],
                "score": config['score'],
                "usedTime": usedTime,
                "answer": answer
            })
        except:
            pass

    def _generate_ms_answer(self, folder, query, config):
        try:
            start = time.time()
            answer = generate_ms_answer(query, folder, config)
            end = time.time()
            usedTime = f"{end - start:.2f}s"
            if answer: self.answers.append({
                "name": config['name'],
                "type": config['type'],
                "model": config['model'],
                "score": config['score'],
                "usedTime": usedTime,
                "answer": answer
            })
        except:
            pass

    def generateAnswer(self, folder):
        reply = {"result": [], "best_answer": {}}
        with open(os.path.join(folder, "problems.txt"), "r", encoding="utf-8") as f:
            problems = ast.literal_eval(f.read().strip())
        query = convert_problems_to_query(problems)
        if not query: return reply
        tasks = []
        with ThreadPoolExecutor(max_workers=threads) as pool:
            for m in [m for m in models if m['enabled']]:
                tp = m['type']
                if tp == 'openai':
                    tasks.append(pool.submit(self._generate_oa_answer, folder, query, m))
                elif tp == 'claude':
                    tasks.append(pool.submit(self._generate_cl_answer, folder, query, m))
                elif tp == 'grok':
                    tasks.append(pool.submit(self._generate_gk_answer, folder, query, m))
                elif tp == 'gemini':
                    tasks.append(pool.submit(self._generate_gm_answer, folder, query, m))
                elif tp == 'cloudflare':
                    tasks.append(pool.submit(self._generate_cf_answer, folder, query, m))
                elif tp == 'openrouter':
                    tasks.append(pool.submit(self._generate_ot_answer, folder, query, m))
                elif tp == 'poixe':
                    tasks.append(pool.submit(self._generate_px_answer, folder, query, m))
                elif tp == 'siliconflow':
                    tasks.append(pool.submit(self._generate_sf_answer, folder, query, m))
                elif tp == 'infinigence':
                    tasks.append(pool.submit(self._generate_ig_answer, folder, query, m))
                elif tp == 'zhipu':
                    tasks.append(pool.submit(self._generate_zp_answer, folder, query, m))
                elif tp == 'dmxapi':
                    tasks.append(pool.submit(self._generate_dm_answer, folder, query, m))
                elif tp == 'modelscope':
                    tasks.append(pool.submit(self._generate_ms_answer, folder, query, m))
                else:
                    continue

            for future in as_completed(tasks):
                try:
                    future.result()
                except Exception as e:
                    print(f"生成失败: {e}")

        if not self.answers: return reply
        for r in self.answers:
            answer_dict = convert_answer_to_dict(r['answer'], problems)
            if answer_dict: reply["result"].append({
                "name": r['name'],
                "type": r['type'],
                "model": r['model'],
                "score": r['score'],
                "usedTime": r['usedTime'],
                "answer_dict": answer_dict,
                "answer": r['answer']
            })
        reply["result"].sort(key=lambda x: -float(x['usedTime'][:-1]))
        best_answer = {}
        for page in problems.keys():
            page_answers = [r['answer_dict'][page] for r in reply['result'] if page in r['answer_dict']]
            scoreList = [r['score'] for r in reply['result'] if page in r['answer_dict']]
            if not page_answers: continue
            tp = problems[page]['problemType']
            if tp == 1:
                best_answer[page] = best_item(page_answers, scoreList)
            elif tp == 2:
                best_answer[page] = best_item(page_answers, scoreList)
            elif tp == 3:
                best_answer[page] = best_item(page_answers, scoreList)
            elif tp == 4:
                new_list = []
                for i in range(min([len(ans) for ans in page_answers])):
                    new_list.append(best_item([[ans[i]] for ans in page_answers], scoreList)[0])
                best_answer[page] = new_list
            elif tp == 5:
                new_list = []
                for i in range(min([len(ans) for ans in page_answers])):
                    new_list.append(best_item([[ans[i]] for ans in page_answers], scoreList)[0])
                best_answer[page] = new_list
            else:
                new_list = []
                for i in range(min([len(ans) for ans in page_answers])):
                    new_list.append(best_item([[ans[i]] for ans in page_answers], scoreList)[0])
                best_answer[page] = new_list
        reply["result"].sort(key=lambda x: float(x['usedTime'][:-1]))
        reply["best_answer"] = best_answer
        return reply

def best_item(lst, scoreList=[]):
    freq = {}
    score = {}
    seen = set()
    unique = []
    for idx, it in enumerate(lst):
        k = tuple(it)
        if k not in seen:
            seen.add(k)
            unique.append(it)
        freq[k] = freq.get(k, 0) + 1
        if scoreList:
            s = score.get(k, 0) + scoreList[idx]
        else:
            s = score.get(k, 0) + 1
        score[k] = s
    unique.sort(key=lambda x: (-score[tuple(x)], -freq[tuple(x)], len(x)))
    return unique[0]

def convert_problems_to_query(problems):
    if not problems:
        return ""
    query_parts = []
    format_parts = []
    pages = list(problems.keys())
    for page, details in problems.items():
        query_part = f"第{page}页是"
        format_part = f"\"{page}\": "
        tp = details['problemType']
        if tp == 1:
            query_part += "单选题,"
            if details.get('body').strip():
                query_part += f"题目是\"{details['body'].strip()}\","
            else:
                query_part += "题目参考该页内容,"
            for index, val in enumerate(details['option_values']):
                if val.strip():
                    query_part += f"选项{details['option_keys'][index]}是\"{val.strip()}\","
                else:
                    query_part += f"选项{details['option_keys'][index]}参考该页内容,"
            query_part += "你应该从\"" + ",".join(details['option_keys']) + "\"中选出最符合的一个选项"
            format_part += f"[\"{details['option_keys'][0]}\"]"
        elif tp == 2:
            query_part += "多选题,"
            if details.get('body').strip():
                query_part += f"题目是\"{details['body'].strip()}\","
            else:
                query_part += "题目参考该页内容,"
            for index, val in enumerate(details['option_values']):
                if val.strip():
                    query_part += f"选项{details['option_keys'][index]}是\"{val.strip()}\","
                else:
                    query_part += f"选项{details['option_keys'][index]}参考该页内容,"
            query_part += "你应该从\"" + ",".join(details['option_keys']) + "\"中选出最符合的一个或多个选项"
            format_part += f"[\"{details['option_keys'][0]}\", \"{details['option_keys'][1]}\"]"
        elif tp == 3:
            query_part += "投票题,"
            if details.get('body').strip():
                query_part += f"题目是\"{details['body'].strip()}\","
            else:
                query_part += "题目参考该页内容,"
            for index, val in enumerate(details['option_values']):
                if val.strip():
                    query_part += f"选项{details['option_keys'][index]}是\"{val.strip()}\","
                else:
                    query_part += f"选项{details['option_keys'][index]}参考该页内容,"
            if details['pollingCount'] > 1:
                query_part += "你应该从\"" + ",".join(details['option_keys']) + "\"中选出最符合的一个或多个选项，最多" + str(details['pollingCount']) + "个选项"
            else:
                query_part += "你应该从\"" + ",".join(details['option_keys']) + "\"中选出最符合的一个选项"
            format_part += f"[\"{details['option_keys'][0]}\"]"
        elif tp == 4:
            query_part += "填空题,"
            if details.get('body').strip():
                query_part += f"题目是\"{details['body'].strip()}\","
            else:
                query_part += "题目参考该页内容,"
            if details['num_blanks'] > 1:
                query_part += f"你应该在\"[填空1]\"至\"[填空{details['num_blanks']}]\"处填上共{details['num_blanks']}个答案"
            else:
                query_part += f"你应该在\"[填空1]\"处填上1个答案"
            format_part += "[" + ", ".join(["\"[填空" + str(i) + "]答案\"" for i in range(1, details['num_blanks'] + 1)]) + "]"
        elif tp == 5:
            query_part += "主观题,"
            if details.get('body').strip():
                query_part += f"题目是\"{details['body'].strip()}\","
            else:
                query_part += "题目参考该页内容,"
            query_part += "你应该结合题目给出一个答案,尽量简明扼要"
            format_part += "[\"主观题答案\"]"
        else:
            query_part += "其它题型,"
            if details.get('body').strip():
                query_part += f"题目是\"{details['body'].strip()}\","
            else:
                query_part += "题目参考该页内容,"
            query_part += "请根据题目内容进行回答"
            format_part += "[\"合适答案\"]"
        query_parts.append(query_part)
        format_parts.append(format_part)
    if not query_parts or not format_parts:
        return ""
    query = "这些是课程文件,请你先仔细阅读完所有内容,理解所有知识后,再严谨准确地解答并只解答以下页码的题目:" + ",".join([str(p) for p in pages]) + "." + ";".join(query_parts) + "."
    query += "解答完毕后可以得到一个字典,键是页码,值是选项列表(适用于单选题,多选题和投票题,单选题应给出含一个选项的列表,如[\"A\"];多选题应给出含一个或多个选项的列表,如[\"A\", \"B\"];投票题应给出含合适个选项的列表,如[\"A\"])或答案列表(适用于填空题,主观题和其它题型,填空题应给出数量与填空处相等的答案的列表,主观题应给出含一个答案的列表,其他题型给出含合适答案的列表),字典必须写成一行字符串.最终答案应该在该字符串前面和后面都加上5个\"~\"."
    query += "最终答案格式可参照如下: ~~~~~{" + ", ".join(format_parts) + "}~~~~~ .按上述要求,请你给出并只给出最终答案."
    return query

def convert_answer_to_dict(answer, problems):
    correction_dict = {}
    if not answer:
        return correction_dict
    new_answer = answer.replace('\\"', '"').replace("\\n", " ").replace("\\t", " ").replace("\\r", " ")
    answer_dicts = re.findall(r'~\s*({.*?})\s*~', new_answer, re.DOTALL)
    pages = list(problems.keys())
    all_answers = {page: [] for page in pages}
    for a in answer_dicts:
        try:
            answer_dict = json.loads(a)
            answer_dict = {int(k): v for k, v in answer_dict.items()}
            for page in [p for p in pages if p in answer_dict]:
                tp = problems[page]['problemType']
                if tp == 1:
                    if not isinstance(answer_dict[page], list):
                        print(f"答案格式错误,第{page}页应为单选题,答案应为含一个选项的列表")
                        continue
                    options = [opt for opt in problems[page]['option_keys'] if opt in answer_dict[page]]
                    if options:
                        all_answers[page].append([options[0]])
                elif tp == 2:
                    if not isinstance(answer_dict[page], list):
                        print(f"答案格式错误,第{page}页应为多选题,答案应为含一个或多个选项的列表")
                        continue
                    options = [opt for opt in problems[page]['option_keys'] if opt in answer_dict[page]]
                    if options:
                        all_answers[page].append(options)
                elif tp == 3:
                    if not isinstance(answer_dict[page], list):
                        print(f"答案格式错误,第{page}页应为投票题,答案应为含一个或多个选项的列表")
                        continue
                    options = [opt for opt in problems[page]['option_keys'] if opt in answer_dict[page]]
                    if options and len(options) <= problems[page]['pollingCount']:
                        all_answers[page].append(options)
                elif tp == 4:
                    if not isinstance(answer_dict[page], list) or len(answer_dict[page]) != problems[page]["num_blanks"]:
                        print(f"答案格式错误,第{page}页应为填空题,答案应为含{problems[page].get('num_blanks', 1)}个答案的列表")
                        continue
                    all_answers[page].append([ans.strip() for ans in answer_dict[page]])
                elif tp == 5:
                    if not isinstance(answer_dict[page], list) or len(answer_dict[page]) != 1:
                        print(f"答案格式错误,第{page}页应为主观题,答案应为含一个答案的列表")
                        continue
                    all_answers[page].append([ans.strip() for ans in answer_dict[page]])
                else:
                    if not isinstance(answer_dict[page], list) or len(answer_dict[page]) < 1:
                        print(f"答案格式错误,第{page}页应为其它题型,答案应为含合适答案的列表")
                        continue
                    all_answers[page].append([ans.strip() for ans in answer_dict[page]])
        except Exception as e:
            print(f"答案格式错误,无法解析: {e}")
    for page in pages:
        if not all_answers.get(page): continue
        tp = problems[page]['problemType']
        if tp == 1:
            correction_dict[page] = best_item(all_answers[page])
        elif tp == 2:
            correction_dict[page] = best_item(all_answers[page])
        elif tp == 3:
            correction_dict[page] = best_item(all_answers[page])
        elif tp == 4:
            new_list = []
            for i in range(min([len(ans) for ans in all_answers[page]])):
                new_list.append(best_item([[ans[i]] for ans in all_answers[page]])[0])
            correction_dict[page] = new_list
        elif tp == 5:
            new_list = []
            for i in range(min([len(ans) for ans in all_answers[page]])):
                new_list.append(best_item([[ans[i]] for ans in all_answers[page]])[0])
            correction_dict[page] = new_list
        else:
            new_list = []
            for i in range(min([len(ans) for ans in all_answers[page]])):
                new_list.append(best_item([[ans[i]] for ans in all_answers[page]])[0])
            correction_dict[page] = new_list
    return correction_dict

def upload_oa_file(folder, config):
    files = [f for f in os.listdir(folder) if f.lower().endswith('.pdf')]
    if not files:
        print("没有PDF文件")
        return None
    filepath = os.path.join(folder, files[0])
    with open(filepath, "rb") as f:
        files ={
            "file": (os.path.basename(filepath), f.read(), "application/pdf")
        }
    data = {
        "purpose": "user_data"
    }
    headers = {
        "Authorization": f"Bearer {config['apiKey']}"
    }
    try:
        r = requests.post("https://api.openai.com/v1/files", headers=headers, files=files, data=data, timeout=timeout)
        r.raise_for_status()
        return r.json()["id"]
    except Exception as e:
        print(f"OpenAI文件上传发生错误: {e}")
        return None

def generate_oa_answer(query, folder, config):
    file_id = upload_oa_file(folder, config)
    if not file_id:
        return None
    content = [
        {"type": "input_text", "text": query},
        {"type": "input_file", "file_id": file_id}
    ]
    headers = {
        "Authorization": f"Bearer {config['apiKey']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": config['model'],
        "max_output_tokens": 10000,
        "input": []
    }
    if config['prompt']:
        payload["input"].append({"role": "system", "content": config['prompt']})
    payload["input"].append({"role": "user", "content": content})
    try:
        r = requests.post("https://api.openai.com/v1/responses", headers=headers, data=json.dumps(payload), timeout=timeout)
        r.raise_for_status()
        text = "\n".join([c.get("content", [])[0].get("text", "") for c in r.json().get("output", [{}]) if c.get("type", "") == "message"]).strip()
    except Exception as e:
        print(f"OpenAI生成回答发生错误: {e}")
        return None
    return text

def upload_cl_file(folder, config):
    files = [f for f in os.listdir(folder) if f.lower().endswith('.pdf')]
    if not files:
        print("没有PDF文件")
        return None
    filepath = os.path.join(folder, files[0])
    headers = {
        "x-api-key": config['apiKey'],
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "files-api-2025-04-14"
    }
    with open(filepath, "rb") as f:
        files ={
            "file": (os.path.basename(filepath), f.read(), "application/pdf")
        }
    try:
        r = requests.post("https://api.anthropic.com/v1/files", headers=headers, files=files, timeout=timeout)
        r.raise_for_status()
        return r.json()["id"]
    except Exception as e:
        print(f"Claude文件上传发生错误: {e}")
        return None

def generate_cl_answer(query, folder, config):
    file_id = upload_cl_file(folder, config)
    if not file_id:
        return None
    content = [
        {"type": "text", "text": query},
        {"type": "document", "source": {"type": "file", "file_id": file_id}, "citations": {"enabled": True}}
    ]
    headers = {
        "x-api-key": config['apiKey'],
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "files-api-2025-04-14",
        "content-type": "application/json"
    }
    payload = {
        "model": config['model'],
        "temperature": config['temperature'],
        "max_tokens": 10000,
        "messages": [
            {"role": "user", "content": content}
        ]
    }
    if config['prompt']:
        payload["system"] = [
            {"type": "text", "text": config['prompt']}
        ]
    try:
        r = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=timeout)
        r.raise_for_status()
        text = "\n".join([c.get("text", "") for c in r.json().get("content", [{}]) if c.get("type", "") == "text"]).strip()
    except Exception as e:
        print(f"Claude生成回答发生错误: {e}")
        return None
    return text

def generate_gk_answer(query, folder, config):
    files = [f for f in os.listdir(folder)
                   if f.lower().endswith('.jpg') and f.lower().startswith('mark_') and os.path.splitext(f)[0][5:].isdigit()]
    files.sort(key=lambda x: int(os.path.splitext(x)[0][5:]))
    files = [os.path.join(folder, f) for f in files]
    content = [
        {"type": "text", "text": query}
    ]
    for f in files:
        with open(f, "rb") as ff:
            image_url = f"data:image/jpeg;base64,{base64.b64encode(ff.read()).decode('utf-8')}"
        content.append({
            "type": "image_url", "image_url": { "url": image_url }
        })
    headers = {
        "Authorization": f"Bearer {config['apiKey']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": config['model'],
        "temperature": config["temperature"],
        "max_tokens": 10000,
        "messages": []
    }
    if config['prompt']:
        payload["messages"].append({"role": "system", "content": config['prompt']})
    payload["messages"].append({"role": "user", "content": content})
    try:
        r = requests.post("https://api.x.ai/v1/chat/completions", headers=headers, data=json.dumps(payload), timeout=timeout)
        r.raise_for_status()
        text = r.json().get("choices", [{}])[0].get("message", {}).get("content", '')
    except Exception as e:
        print(f"Grok生成回答发生错误: {e}")
        return None
    return text

def upload_gm_file(folder, config):
    files = [f for f in os.listdir(folder) if f.lower().endswith('.pdf')]
    if not files:
        print("没有PDF文件")
        return None
    filepath = os.path.join(folder, files[0])
    with open(filepath, "rb") as f:
        data = f.read()
    display_name = os.path.basename(filepath)
    headers1 = {
        "X-Goog-Upload-Protocol": "resumable",
        "X-Goog-Upload-Command": "start",
        "X-Goog-Upload-Header-Content-Length": str(len(data)),
        "X-Goog-Upload-Header-Content-Type": "application/pdf",
        "Content-Type": "application/json",
    }
    headers2 = {
        "Content-Length": str(len(data)),
        "X-Goog-Upload-Offset": "0",
        "X-Goog-Upload-Command": "upload, finalize",
    }
    body = {"file": {"display_name": display_name}}
    try:
        r1 = requests.post(f"https://generativelanguage.googleapis.com/upload/v1beta/files?key={config['apiKey']}", headers=headers1, data=json.dumps(body), timeout=timeout)
        r1.raise_for_status()
        upload_url = r1.headers["X-Goog-Upload-Url"]
        r2 = requests.post(upload_url, headers=headers2, data=data, timeout=timeout)
        r2.raise_for_status()
        return r2.json()['file']['uri']
    except Exception as e:
        print(f"Gemini文件上传发生错误: {e}")
        return None

def generate_gm_answer(query, folder, config):
    file_uri = upload_gm_file(folder, config)
    if not file_uri:
        return None
    parts = [
        {"file_data": {"file_uri": file_uri, "mime_type": "application/pdf"}}
    ]
    if config['prompt']:
        parts.append({"text": config['prompt']})
    parts.append({"text": query})
    payload = {
        "generationConfig": {
            "temperature": config["temperature"],
            "maxOutputTokens": 10000
        },
        "contents": [{"role": "user", "parts": parts}]
    }
    try:
        r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{config['model']}:generateContent?key={config['apiKey']}", headers={"Content-Type": "application/json"}, data=json.dumps(payload))
        r.raise_for_status()
        text = "".join(p.get("text", "") for p in r.json().get("candidates", [{}])[0].get("content", {}).get("parts", []) if p.get("text"))
    except Exception as e:
        print(f"Gemini生成回答发生错误: {e}")
        return None
    return text

def generate_cf_answer(query, folder, config):
    files = [f for f in os.listdir(folder)
                   if f.lower().endswith('.jpg') and f.lower().startswith('resized_') and os.path.splitext(f)[0][8:].isdigit()]
    files.sort(key=lambda x: int(os.path.splitext(x)[0][8:]))
    files = [os.path.join(folder, f) for f in files]
    ppt = []
    headers = {
        "Authorization": f"Bearer {config['apiToken']}",
        "Content-Type": "application/json"
    }
    if os.path.exists(os.path.join(folder, "ppt.txt")):
        with open(os.path.join(folder, "ppt.txt"), "r", encoding="utf-8") as f:
            ppt = f.read().splitlines()
    else:
        for i in range(math.ceil(len(files)/10)):
            images = files[i*10:(i+1)*10]
            payload = []
            for img in images:
                with open(img, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                    payload.append({
                        "temperature": config['temperature'],
                        "max_tokens": 500,
                        "messages": [{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": f"请叙述本图全部内容,要求:1)完整复述所有文字,尽量不修改;2)若有标题/表格/图表尽量提及;3)不要发挥.标注页码:第{os.path.splitext(os.path.basename(img))[0][8:]}页."},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                            ]
                        }]
                    })
                if config['prompt']:
                    payload[-1]["messages"].append({"role": "system", "content": config['prompt']})
            r = requests.post(f"https://api.cloudflare.com/client/v4/accounts/{config['accountId']}/ai/run/{config['model']}?queueRequest=true", headers=headers, data=json.dumps({"requests": payload}), timeout=timeout)
            r.raise_for_status()
            request_id = r.json()["result"]["request_id"]
            start = time.time()
            while True:
                time.sleep(2)
                if time.time() - start > timeout:
                    print("Cloudflare轮询请求超时")
                    break
                try:
                    p = requests.post(f"https://api.cloudflare.com/client/v4/accounts/{config['accountId']}/ai/run/{config['model']}?queueRequest=true", headers=headers, data=json.dumps({"request_id": request_id}), timeout=timeout)
                    p.raise_for_status()
                    if "responses" in p.json()["result"]:
                        result_obj = p.json()["result"]
                        responses = result_obj.get("responses", [])
                        responses.sort(key=lambda x: int(x["id"]))
                        base_page = int(os.path.splitext(os.path.basename(images[0]))[0][8:])
                        
                        for resp in responses:
                            ppt.append(str({"页码": base_page + int(resp["id"]), "内容": resp["result"]["response"]}))
                        break
                except Exception as e:
                    print(f"Cloudflare轮询请求发生错误: {e}")

    if ppt:
        if not os.path.exists(os.path.join(folder, "ppt.txt")):
            with open(os.path.join(folder, "ppt.txt"), "w", encoding="utf-8") as f:
                f.write("\n".join(ppt))
    else:
        if os.path.exists(os.path.join(folder, "ppt.txt")):
            os.remove(os.path.join(folder, "ppt.txt"))
        print("Cloudflare未生成PPT文本")
        return None

    filepath = os.path.join(folder, "grid.jpg")
    if not os.path.exists(filepath):
        print(f"文件 {filepath} 不存在")
        return None
    with open(filepath, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    data_uri = f"data:image/jpeg;base64,{b64}"
    content = [
        {"type": "text", "text": query},
        {"type": "text", "text": "\n".join(ppt)},
        {"type": "image_url", "image_url": {"url": data_uri}}
    ]
    payload = {
        "temperature": config['temperature'],
        "max_tokens": 10000,
        "messages": []
    }
    if config['prompt']:
        payload["messages"].append({"role": "system", "content": config['prompt']})
    payload["messages"].append({"role": "user", "content": content})
    try:
        r = requests.post(f"https://api.cloudflare.com/client/v4/accounts/{config['accountId']}/ai/run/{config['model']}", headers=headers, data=json.dumps(payload), timeout=timeout)
        r.raise_for_status()
        text = r.json().get("result", {}).get("response", '')
    except Exception as e:
        print(f"Cloudflare生成回答发生错误: {e}")
        return None
    return text

def generate_ot_answer(query, folder, config):
    files = [f for f in os.listdir(folder) if f.lower().endswith('.pdf')]
    if not files:
        print("没有PDF文件")
        return None
    filepath = os.path.join(folder, files[0])
    with open(filepath, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    data_uri = f"data:application/pdf;base64,{b64}"
    content = [
        {"type": "text", "text": query},
        {"type": "file", "file": {"filename": os.path.basename(filepath), "file_data": data_uri}}
    ]
    headers = {
        "Authorization": f"Bearer {config['apiKey']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": config['model'],
        "temperature": config['temperature'],
        "max_tokens": 10000,
        "transforms": ["middle-out"],
        "messages": []
    }
    if config['prompt']:
        payload["messages"].append({"role": "system", "content": config['prompt']})
    payload["messages"].append({"role": "user", "content": content})
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, data=json.dumps(payload), timeout=timeout)
        r.raise_for_status()
        text = r.json().get("choices", [{}])[0].get("message", {}).get("content", '')
    except Exception as e:
        print(f"OpenRouter生成回答发生错误: {e}")
        return None
    return text

def generate_px_answer(query, folder, config):
    filepath = os.path.join(folder, "long.jpg")
    if not os.path.exists(filepath):
        print(f"文件 {filepath} 不存在")
        return None
    with open(filepath, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    data_uri = f"data:image/jpeg;base64,{b64}"
    content = [
        {"type": "text", "text": query},
        {"type": "image_url", "image_url": {"url": data_uri}}
    ]
    headers = {
        "Authorization": f"Bearer {config['apiKey']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": config['model'],
        "temperature": config['temperature'],
        "max_tokens": 10000,
        "messages": []
    }
    if config['prompt']:
        payload["messages"].append({"role": "system", "content": config['prompt']})
    payload["messages"].append({"role": "user", "content": content})
    try:
        r = requests.post("https://api.poixe.com/v1/chat/completions", headers=headers, data=json.dumps(payload), timeout=timeout)
        r.raise_for_status()
        text = r.json().get("choices", [{}])[0].get("message", {}).get("content", '')
    except Exception as e:
        print(f"Poixe生成回答发生错误: {e}")
        return None
    return text

def generate_sf_answer(query, folder, config):
    filepath = os.path.join(folder, "long.jpg")
    if not os.path.exists(filepath):
        print(f"文件 {filepath} 不存在")
        return None
    with open(filepath, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    data_uri = f"data:image/jpeg;base64,{b64}"
    content = [
        {"type": "text", "text": query},
        {"type": "image_url", "image_url": {"url": data_uri}}
    ]
    headers = {
        "Authorization": f"Bearer {config['apiKey']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": config['model'],
        "temperature": config['temperature'],
        "max_tokens": 10000,
        "messages": []
    }
    if config['prompt']:
        payload["messages"].append({"role": "system", "content": config['prompt']})
    payload["messages"].append({"role": "user", "content": content})
    try:
        r = requests.post("https://api.siliconflow.cn/v1/chat/completions", headers=headers, data=json.dumps(payload), timeout=timeout)
        r.raise_for_status()
        text = r.json().get("choices", [{}])[0].get("message", {}).get("content", '')
    except Exception as e:
        print(f"SiliconFlow生成回答发生错误: {e}")
        return None
    return text

def generate_ig_answer(query, folder, config):
    filepath = os.path.join(folder, "long.jpg")
    if not os.path.exists(filepath):
        print(f"文件 {filepath} 不存在")
        return None
    with open(filepath, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    data_uri = f"data:image/jpeg;base64,{b64}"
    content = [
        {"type": "text", "text": query},
        {"type": "image_url", "image_url": {"url": data_uri}}
    ]
    headers = {
        "Authorization": f"Bearer {config['apiKey']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": config['model'],
        "temperature": config['temperature'],
        "max_tokens": 10000,
        "messages": []
    }
    if config['prompt']:
        payload["messages"].append({"role": "system", "content": config['prompt']})
    payload["messages"].append({"role": "user", "content": content})
    try:
        r = requests.post(f"https://cloud.infini-ai.com/maas/v1/chat/completions", headers=headers, data=json.dumps(payload), timeout=timeout)
        r.raise_for_status()
        text = r.json().get("choices", [{}])[0].get("message", {}).get("content", '')
    except Exception as e:
        print(f"InfiniGence生成回答发生错误: {e}")
        return None
    return text

def generate_zp_answer(query, folder, config):
    filepath = os.path.join(folder, "long.jpg")
    if not os.path.exists(filepath):
        print(f"文件 {filepath} 不存在")
        return None
    with open(filepath, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    data_uri = f"data:image/jpeg;base64,{b64}"
    content = [
        {"type": "text", "text": query},
        {"type": "image_url", "image_url": {"url": data_uri}}
    ]
    headers = {
        "Authorization": f"Bearer {config['apiKey']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": config['model'],
        "temperature": config['temperature'],
        "max_tokens": 10000,
        "messages": []
    }
    if config['prompt']:
        payload["messages"].append({"role": "system", "content": config['prompt']})
    payload["messages"].append({"role": "user", "content": content})
    try:
        r = requests.post("https://open.bigmodel.cn/api/paas/v4/chat/completions", headers=headers, data=json.dumps(payload), timeout=timeout)
        r.raise_for_status()
        text = r.json().get("choices", [{}])[0].get("message", {}).get("content", '')
    except Exception as e:
        print(f"ZhiPu生成回答发生错误: {e}")
        return None
    return text

def generate_dm_answer(query, folder, config):
    filepath = os.path.join(folder, "long.jpg")
    if not os.path.exists(filepath):
        print(f"文件 {filepath} 不存在")
        return None
    with open(filepath, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    data_uri = f"data:image/jpeg;base64,{b64}"
    content = [
        {"type": "text", "text": query},
        {"type": "image_url", "image_url": {"url": data_uri}}
    ]
    headers = {
        "Accept": "application/json",
        "Authorization": config['apiKey'],
        "User-Agent": "DMXAPI/1.0.0",
        "Content-Type": "application/json"
    }
    payload = {
        "model": config['model'],
        "temperature": config['temperature'],
        "max_tokens": 10000,
        "messages": []
    }
    if config['prompt']:
        payload["messages"].append({"role": "system", "content": config['prompt']})
    payload["messages"].append({"role": "user", "content": content})
    try:
        r = requests.post("https://www.dmxapi.cn/v1/chat/completions", headers=headers, data=json.dumps(payload), timeout=timeout)
        r.raise_for_status()
        text = r.json().get("choices", [{}])[0].get("message", {}).get("content", '')
    except Exception as e:
        print(f"DMXAPI生成回答发生错误: {e}")
        return None
    return text

def generate_ms_answer(query, folder, config):
    filepath = os.path.join(folder, "long.jpg")
    if not os.path.exists(filepath):
        print(f"文件 {filepath} 不存在")
        return None
    with open(filepath, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    data_uri = f"data:image/jpeg;base64,{b64}"
    content = [
        {"type": "text", "text": query},
        {"type": "image_url", "image_url": {"url": data_uri}}
    ]
    headers = {
        "Authorization": f"Bearer {config['accessToken']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": config['model'],
        "temperature": config['temperature'],
        "max_tokens": 10000,
        "messages": []
    }
    if config['prompt']:
        payload["messages"].append({"role": "system", "content": config['prompt']})
    payload["messages"].append({"role": "user", "content": content})
    try:
        r = requests.post("https://api-inference.modelscope.cn/v1/chat/completions", headers=headers, data=json.dumps(payload), timeout=timeout)
        r.raise_for_status()
        text = r.json().get("choices", [{}])[0].get("message", {}).get("content", '')
    except Exception as e:
        print(f"ModelScope生成回答发生错误: {e}")
        return None
    return text

if __name__ == "__main__":
    folder = "1529274209982060032"
    with open(os.path.join(folder, "problems.txt"), "r", encoding="utf-8") as f:
        problems = ast.literal_eval(f.read().strip())
    reply = LLMManager().generateAnswer(folder)
    reply_text = "LLM答案列表:\n"
    for key in problems.keys():
        reply_text += "-"*20 + "\n"
        problemType = {1:"单选题", 2:"多选题", 3:"投票题", 4:"填空题", 5:"主观题"}.get(problems[key]['problemType'], "其它题型")
        reply_text += f"PPT: 第{key}页 {problemType} {problems[key].get('score', 0)}分\n"
        if reply['best_answer'].get(key):
            reply_text += f"最佳答案: {reply['best_answer'][key]}\n所有答案:\n"
            for r in reply["result"]:
                if r["answer_dict"].get(key):
                    reply_text += f"[{r['score']}, {r['usedTime']}] {r['name']}: {r['answer_dict'][key]}\n"
        else:
            reply_text += f"无答案\n"
    print(reply_text)
