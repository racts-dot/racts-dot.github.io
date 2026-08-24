// Deploy this bound to the Resale Tracker — LIVE spreadsheet (script.google.com).
// See DEPLOY-INSTRUCTIONS.txt in this same folder for the exact steps.

var SHEET_ID = '1ZUvi_jA--rzVlR6fWKVEx3jecCa8jGKeRDOr72dUjXI';
var TAB_NAME = 'Sales';
var SECRET_TOKEN = '81c16dd30f6a0b27b10a1aa6e59c17d361a643c4';

function doPost(e) {
  var out = { ok: false };
  try {
    var body = JSON.parse(e.postData.contents);

    if (body.token !== SECRET_TOKEN) {
      out.error = 'bad token';
      return respond(out);
    }

    var sh = SpreadsheetApp.openById(SHEET_ID).getSheetByName(TAB_NAME);
    var data = sh.getDataRange().getValues();
    var header = data[0];
    var numCol = header.indexOf('#');

    var rowValues = {
      '#': body.num,
      'Item': body.title || '',
      'Category': body.category || '',
      'Channel': body.channel || 'Facebook',
      'Status': body.status || '',
      'Order date': body.orderdate || '',
      'Sold date': body.solddate || '',
      'Week': body.week || '',
      'Cost': body.cost || '',
      'Received': body.received || '',
      'Net': body.net || '',
      'Account': body.device || '',
      'Recipient/Buyer': body.buyer || '',
      'Supplier': body.supplier || '',
      'Carrier & Tracking': body.track || '',
      'Order ID': body.oid || '',
      'Batch': body.batch || '',
      'Notes': body.notes || ''
    };
    var rowArr = header.map(function (h) {
      return Object.prototype.hasOwnProperty.call(rowValues, h) ? rowValues[h] : '';
    });

    var rowIdx = -1;
    for (var i = 1; i < data.length; i++) {
      if (String(data[i][numCol]) === String(body.num)) { rowIdx = i + 1; break; }
    }

    if (rowIdx > 0) {
      sh.getRange(rowIdx, 1, 1, rowArr.length).setValues([rowArr]);
      out.updated = true;
    } else {
      sh.appendRow(rowArr);
      out.updated = false;
    }
    out.ok = true;
  } catch (err) {
    out.error = String(err);
  }
  return respond(out);
}

function respond(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
