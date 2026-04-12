#!/usr/bin/env python3
import json
import logging
import traceback
import uuid
import requests
import base64 as b64
import hashlib
import os
from copy import deepcopy

from ctf_gameserver import checkerlib
from checklib import *
from utils import *

FRONTEND_PORT = 3000
BACKEND_PORT = 3001

os.makedirs('data', exist_ok=True)
STATE_KEY_PREFIX = "ccforms1"

def check_sla(host):

    try:
        '''
        r = requests.get(f'http://{host}:{FRONTEND_PORT}')

        if r.status_code != 200:
            quit(Status.DOWN, 'Frontend is down', r.text)

        if not '<title>CCForms</title>' in r.text:
            quit(Status.DOWN, 'Unexpected home page response', r.text)
        '''
        r = requests.get(f'http://{host}:{BACKEND_PORT}')

        if r.status_code != 200:
            quit(Status.DOWN, 'Backend is down', r.text)
        
    
        
        if not 'Hello, world!' in r.text or r.headers.get('Access-Control-Allow-Origin') != '*':
            quit(Status.DOWN, 'Unexpected backend response', r.text)
        
        
        client = ClientSession(host, BACKEND_PORT)
        client2 = ClientSession(host, BACKEND_PORT)

        client.register()
        client.login()

        form1 = client.new_form()
        form1_g = client.get_form(form1['id'])

        if form1 != form1_g:
            quit(Status.DOWN, 'Failed to get form', f'Retrieved: {form1_g}, expected: {form1}')        
        
        ans1id, ans1 = client.submit_answer(form1)

        if random.randint(0,100) < 50:
            client.login()

        answers_f1 = client.get_answers(form1)
        
        ans1_g = answers_f1[0]['answer']

        filetested = False

        for i in range(len(form1['questions'])):
            if form1['questions'][i]['type'] == 'file':
                ans1[i]['file_id'] = ans1_g[i]['file_id']
                ans1_g[i]['content'] = ans1[i]['content']

                file = client.get_file(ans1[i]['file_id'])
                if b64.b64decode(ans1[i]['content']) != file:
                    quit(Status.DOWN, 'Failed to get file', f'Retrieved: {file}, expected: {ans1[i]["content"]}')
                
                filetested = True
                
                
        if answers_f1[0]['answer'] != ans1:
            quit(Status.DOWN, 'Failed to get answers', f'Retrieved: {answers_f1}, expected: {ans1}')

        forms = client.get_forms()

        found = False
        for f in forms:
            if f['id'] == form1['id'] and f['title'] == form1['title']:
                found = True
                break
        
        if not found:
            quit(Status.DOWN, 'Failed to get forms', f'Retrieved: {forms}, expected: {form1}')

        client2.register()
        if random.randint(0,100) < 50:
            client2.login()
        
        forms2 = [client2.new_form()]
        answers2 = []
        for _ in range(random.randint(5, 10)):
            action = random.choice(['new', 'get_form', 'get_forms', 'submit_answer', 'get_answers', 'get_file'])
            #print(action)

            if action == 'new':
                form2 = client2.new_form()
                forms2.append(form2)

            if action == 'get_form':
                form_to_check = deepcopy(random.choice(forms2))
                newquestions = []
                for q in form_to_check['questions']:
                    if q['type'] == 'embedded':
                        embedded_form_id = q['data']['id']
                        embedded_form = next(filter(lambda x: x['id'] == embedded_form_id, forms2))
                        newquestions += embedded_form['questions']
                    else:
                        newquestions.append(q)

                form_to_check['questions'] = newquestions
                form_to_check_g = client2.get_form(form_to_check['id'])
                if form_to_check != form_to_check_g:
                    quit(Status.DOWN, 'Failed to get form', f'Retrieved: {form_to_check_g}, expected: {form_to_check}')
        
            if action == 'get_forms':
                expected_forms = []
                for f in forms2:
                    expected_forms.append({'id': f['id'], 'title': f['title']})
                forms_g = client2.get_forms()
                forms_g.sort(key=lambda x: x['id'])
                expected_forms.sort(key=lambda x: x['id'])
                if expected_forms != forms_g:
                    quit(Status.DOWN, 'Failed to get forms', f'Retrieved: {forms_g}, expected: {expected_forms}')

            if action == 'submit_answer':
                client_ans = ClientSession(host, BACKEND_PORT)
                client_ans.register()

                form_to_check = deepcopy(random.choice(forms2))
                newquestions = []
                for q in form_to_check['questions']:
                    if q['type'] == 'embedded':
                        embedded_form_id = q['data']['id']
                        embedded_form = next(filter(lambda x: x['id'] == embedded_form_id, forms2))
                        newquestions += embedded_form['questions']
                    else:
                        newquestions.append(q)

                form_to_check['questions'] = newquestions

                ans_id, ans = client_ans.submit_answer(form_to_check)
                answers2.append({'form_id': form_to_check['id'], 'answer': ans, 'id': ans_id})

            if action == 'get_answers':
                f = random.choice(forms2)
                answers_g = client2.get_answers(f)
                answers = [a['answer'] for a in list(filter(lambda x: x['form_id'] == f['id'], deepcopy(answers2)))]
                

                for x in answers:
                    for a in x:
                        if type(a) == dict and 'content' in a:
                            del a['content']
                for x in answers_g:
                    for a in x['answer']:
                        if type(a) == dict and 'file_id' in a:
                            del a['file_id']

                answers_g__ = list(map(lambda x: x['answer'], answers_g))
                
                for ans in answers:
                    found = False
                    for ans_g in answers_g__:
                        if ans_g == ans:
                            found = True
                            break    
                    if not found:
                        quit(Status.DOWN, 'Failed to get answers', f'Retrieved: {answers_g__}, expected: {answers}')

            if action == 'get_file':
                form = None
                content = None
                ans_id = None
                for ans in answers2:
                    for a in ans['answer']:
                        if type(a) == dict and 'content' in a:
                            content = a['content']
                            ans_id = ans['id']
                            form = next(filter(lambda x: x['id'] == ans['form_id'], forms2))
                            break
                    if form is not None:
                        break

                if form is not None:
                    answers_g = client2.get_answers(form)
                    ans_g = next(filter(lambda x: x['id'] == ans_id, answers_g))
                    
                    found = False
                    for a in ans_g['answer']:
                        if  type(a) == dict and 'file_id' in a:
                            found = True
                            file = client2.get_file(a['file_id'])
                            if b64.b64decode(content) != file:
                                quit(Status.DOWN, 'Failed to get file', f'Retrieved: {file}, expected: {content}')
                            break
                    
                    if not found:
                        quit(Status.DOWN, 'Failed to get file', f'File not found in answers: {ans_g}')
        
        answers_f1_2 = []
        for _ in range(random.randint(2, 5)):
            id, ans = client2.submit_answer(form1)
            answers_f1_2.append({'id': id, 'answer': ans})

        answers_f1 = client.get_answers(form1)

        for ans in answers_f1_2:
            ans_g = next(filter(lambda x: x['id'] == ans['id'], answers_f1))

            for a in ans['answer']:
                if type(a) == dict and 'content' in a:
                    del a['content']
            for a in ans_g['answer']:
                if type(a) == dict and 'file_id' in a:
                    del a['file_id']

            if ans_g['answer'] != ans['answer']:
                quit(Status.DOWN, 'Failed to get answers', f'Retrieved: {answers_f1}, expected: {answers_f1_2}')
            
        ans1_g = answers_f1[0]['answer']

    except Exception as e:         
        quit(Status.DOWN, 'Service is down', traceback.format_exc() )


def put_flag(host, flag, tick):

    client = ClientSession(host, BACKEND_PORT)
    user_id = client.register()
    form = client.new_form(note=flag)

    # check if id is a uuid
    if not is_uuid(user_id):
        quit(Status.DOWN, 'Failed to register user, invalid user id', f'Invalid user id - {user_id}')

    checkerlib.store_state(
        f"{STATE_KEY_PREFIX}:{tick}",
        {"creds": client.export_credentials(), "form_id": form["id"], "user_id": user_id},
    )
    checkerlib.set_flagid(json.dumps({"user_id": user_id, "form_id": form["id"]}))


def get_flag(host, flag, tick):
    state = checkerlib.load_state(f"{STATE_KEY_PREFIX}:{tick}")
    if state is None:
        return False
    creds = state["creds"]
    form_id = state["form_id"]

    client = ClientSession(host, BACKEND_PORT, creds)
    client.login()

    form = client.get_form(form_id)

    for q in form['questions']:
        if "note" in q and q["note"] == flag:
            return True
    return False

def _map_legacy_system_exit(exc: SystemExit) -> checkerlib.CheckResult:
    try:
        code = int(exc.code)
    except Exception:  # noqa: BLE001
        code = Status.ERROR.value

    if code == Status.OK.value:
        return checkerlib.CheckResult.OK
    if code == Status.DOWN.value:
        return checkerlib.CheckResult.DOWN
    return checkerlib.CheckResult.FAULTY


class CCForms1Checker(checkerlib.BaseChecker):

    def place_flag(self, tick):
        flag = checkerlib.get_flag(tick)
        try:
            put_flag(self.ip, flag, tick)
            return checkerlib.CheckResult.OK
        except SystemExit as exc:
            return _map_legacy_system_exit(exc)
        except Exception:  # noqa: BLE001
            logging.exception("CCForms-1 place_flag failed")
            return checkerlib.CheckResult.DOWN

    def check_service(self):
        try:
            check_sla(self.ip)
            return checkerlib.CheckResult.OK
        except SystemExit as exc:
            return _map_legacy_system_exit(exc)
        except Exception:  # noqa: BLE001
            logging.exception("CCForms-1 check_service failed")
            return checkerlib.CheckResult.DOWN

    def check_flag(self, tick):
        flag = checkerlib.get_flag(tick)
        try:
            if get_flag(self.ip, flag, tick):
                return checkerlib.CheckResult.OK
            return checkerlib.CheckResult.FLAG_NOT_FOUND
        except SystemExit as exc:
            result = _map_legacy_system_exit(exc)
            if result == checkerlib.CheckResult.DOWN:
                return checkerlib.CheckResult.FLAG_NOT_FOUND
            return result
        except Exception:  # noqa: BLE001
            logging.exception("CCForms-1 check_flag failed")
            return checkerlib.CheckResult.DOWN


if __name__ == '__main__':
    checkerlib.run_check(CCForms1Checker)
