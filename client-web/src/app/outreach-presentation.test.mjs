import test from "node:test";
import assert from "node:assert/strict";
import { presentOutreachRow, presentOutreachStatus, selectOutreachTotal } from "./outreach-presentation.ts";
test("outreach metric preserves missing as unavailable", () => { assert.equal(selectOutreachTotal({applications:{}, outreach:{total:2}, campaigns:{}, tasks:{open:0}}), 2); assert.equal(selectOutreachTotal({applications:{}, outreach:{}, campaigns:{}, tasks:{open:0}}), null); });
test("outreach presentation excludes internal fields", () => { assert.equal(presentOutreachStatus("POSITIVE_REPLY"), "Positive reply"); const row = presentOutreachRow({id:"1",campaign:"c",company_name:"Acme",contact_name:"A",channel:"EMAIL",status:"SENT",sent_at:null,delivered_at:null,bounced_at:null,reply_at:null,follow_up_due_at:null,subject:"x",body:"x",notes:"x",thread_reference:"x",contact:"x"}); assert.equal("body" in row, false); assert.equal("contact" in row, false); });
