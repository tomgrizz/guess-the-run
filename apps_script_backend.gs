/**
 * Run Pool 2026 — guess-logging backend.
 * Paste this whole file into a Google Apps Script bound to a Google Sheet
 * (Extensions → Apps Script), then deploy as a Web App. Steps in README.md.
 *
 * POST  (from the site)  : appends one entry row [timestamp_ms, name, ganaraska, credit]
 * GET ?callback=fn       : returns all entries as JSONP (the site dedupes to latest-per-name)
 */

var SHEET_NAME = 'entries';

function sheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(SHEET_NAME);
  if (!sh) {
    sh = ss.insertSheet(SHEET_NAME);
    sh.appendRow(['ts', 'name', 'gan', 'cre', 'received']);
  }
  return sh;
}

function clean_(v, maxLen) {
  var s = String(v == null ? '' : v).slice(0, maxLen);
  // neutralize spreadsheet formula injection
  if (/^[=+\-@]/.test(s)) s = "'" + s;
  return s;
}

function doPost(e) {
  var out = { ok: false };
  try {
    var d = JSON.parse(e.postData.contents);
    var name = clean_(d.name, 40).trim();
    var gan = Math.round(Number(d.gan));
    var cre = Math.round(Number(d.cre));
    var ts = Number(d.ts) || Date.now();
    if (name.length >= 2 && isFinite(gan) && isFinite(cre) &&
        gan >= 0 && gan <= 500000 && cre >= 0 && cre <= 500000) {
      sheet_().appendRow([ts, name, gan, cre, new Date()]);
      out.ok = true;
    } else {
      out.error = 'rejected: bad name or numbers';
    }
  } catch (err) {
    out.error = String(err);
  }
  return ContentService.createTextOutput(JSON.stringify(out))
      .setMimeType(ContentService.MimeType.JSON);
}

function doGet(e) {
  var rows = sheet_().getDataRange().getValues().slice(1); // drop header
  var entries = rows.map(function (r) {
    return { ts: Number(r[0]), name: String(r[1]), gan: Number(r[2]), cre: Number(r[3]) };
  }).filter(function (r) {
    return r.name && isFinite(r.gan) && isFinite(r.cre);
  });
  var cb = (e && e.parameter && e.parameter.callback) || '';
  var body = JSON.stringify(entries);
  if (/^[A-Za-z_$][\w$]*$/.test(cb)) {
    return ContentService.createTextOutput(cb + '(' + body + ')')
        .setMimeType(ContentService.MimeType.JAVASCRIPT);
  }
  return ContentService.createTextOutput(body)
      .setMimeType(ContentService.MimeType.JSON);
}
