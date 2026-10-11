import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SubmissionConfirmationTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node is required')
    def test_persistent_exact_page_set_and_explicit_resolution(self):
        subprocess.run(['node', '-e', r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('site/app.js','utf8');
const pages=[{page_id:'a',view:'f1',leaf:1},{page_id:'b',view:'f2',leaf:2},{page_id:'c',view:'f3',leaf:3}];
const store=new Map(),statuses=new Map([['a','awaiting'],['b','awaiting'],['c','draft']]);
const dialog={open:false,showModal(){this.open=true},close(){this.open=false}};
const copyDialog={close(){}};const label={textContent:''};
const context=vm.createContext({state:{corpus:{pages},byLeaf:new Map(pages.map(p=>[p.leaf,p])),currentPage:null},
 storageJSON:key=>store.get(key),submissionStorageKey:p=>'status:'+p.page_id,
 localStorage:{setItem:(k,v)=>store.set(k,JSON.parse(v)),removeItem:k=>store.delete(k)},
 document:{visibilityState:'visible',querySelector:()=>null},
 $:id=>id==='#submission-confirmation-dialog'?dialog:id==='#submission-dialog'?copyDialog:label,
 persistSubmission:(p,status)=>statuses.set(p.page_id,status),renderGrid:()=>{},updateSubmitBar:()=>{}});
for(const name of ['restoreSubmissionConfirmations','showSubmissionConfirmation','resolveSubmissionConfirmation']){
 const start=source.indexOf(`function ${name}(`),end=source.indexOf('\n}',start)+2;
 vm.runInContext(source.slice(start,end),context);
}
store.set('nippo-batch-awaiting',[1,2]);store.set('status:a',{status:'awaiting'});store.set('status:b',{status:'awaiting'});
vm.runInContext('restoreSubmissionConfirmations();showSubmissionConfirmation()',context);
assert.equal(dialog.open,true);assert.equal(label.textContent,'f1, f2');
dialog.close();vm.runInContext('showSubmissionConfirmation()',context);assert.equal(dialog.open,true);
// A new page selection or current page does not change the pending set.
context.state.currentPage=pages[2];
vm.runInContext('resolveSubmissionConfirmation(false)',context);
assert.equal(statuses.get('a'),'draft');assert.equal(statuses.get('b'),'draft');assert.equal(statuses.get('c'),'draft');
assert.equal(dialog.open,false);assert.deepStrictEqual(store.get('nippo-submission-confirmations-v1'),[]);
store.set('nippo-submission-confirmations-v1',[{pageIds:['a'],views:['f1'],batch:false},{pageIds:['b'],views:['f2'],batch:false}]);
vm.runInContext('showSubmissionConfirmation();resolveSubmissionConfirmation(true)',context);
assert.equal(statuses.get('a'),'submitted');assert.equal(statuses.get('b'),'draft');
assert.equal(dialog.open,true);assert.equal(label.textContent,'f2');
vm.runInContext('resolveSubmissionConfirmation(false)',context);assert.equal(dialog.open,false);
assert(source.includes("addEventListener('cancel', event => event.preventDefault())"));
assert(fs.readFileSync('site/index.html','utf8').includes('closedby="none"'));
"""], cwd=ROOT, check=True)
