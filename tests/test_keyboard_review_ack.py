"""No-change acknowledgements use visited body rows, not scroll position."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class KeyboardReviewAcknowledgementTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node is required')
    def test_visit_completion_baseline_and_undo_reset(self):
        subprocess.run(['node', '-e', r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('site/app.js','utf8');
const page={page_id:'p',processed:true,transcription_version:'v1',zones:[
  {kind:'column',lines:[{id:'a'},{id:'b'}]},
  {kind:'column',lines:[{id:'c'}]},
  {kind:'running_header',lines:[{id:'h'}]}]};
let submission={status:'draft',reviewed_no_changes:false},edits={},writes=0;
const context=vm.createContext({state:{currentPage:page},reviewVisits:{},REVIEW_VISITS_KEY:'visits',
 sessionStorage:{setItem:()=>{}},pageSubmission:()=>submission,pageEdits:()=>edits,
 persistSubmission:()=>writes++});
for(const name of ['saveReviewVisits','resetReviewVisits','acknowledgeNoChangeReview','recordReviewVisit']){
 const start=source.indexOf(`function ${name}(`),end=source.indexOf('\n}',start)+2;
 vm.runInContext(source.slice(start,end),context);
}
function visit(id){context.row={dataset:{line:id}};vm.runInContext('recordReviewVisit(row)',context);}
visit('h');visit('a');visit('a');visit('b');assert.equal(writes,0);
edits={a:{after:'changed'}};visit('c');assert.equal(writes,0);
edits={};visit('c');assert.equal(submission.reviewed_no_changes,true);
submission.reviewed_no_changes=false;vm.runInContext('resetReviewVisits(state.currentPage)',context);
visit('c');assert.equal(submission.reviewed_no_changes,false);
visit('a');page.transcription_version='v2';visit('b');assert.equal(submission.reviewed_no_changes,false);
visit('c');visit('a');assert.equal(submission.reviewed_no_changes,true);
submission={status:'submitted',reviewed_no_changes:false};visit('b');assert.equal(submission.reviewed_no_changes,false);
submission.status='draft';page.review_blocked=true;visit('b');assert.equal(submission.reviewed_no_changes,false);
"""], cwd=ROOT, check=True)
