/**
 * Creates the two ranking forms (Bigs, Littles) and one Google Sheet that
 * collects responses from both.
 *
 * 1. Go to https://script.google.com, click "New project".
 * 2. Replace everything in the editor with this file.
 * 3. Fill in BIGS and LITTLES below (exact names, spelled how you want them).
 *    Keep your filled-in copy as create_forms.local.gs (gitignored) so real
 *    names never get committed.
 * 4. Pick createForms in the function dropdown and click Run. Approve access.
 * 5. The execution log at the bottom shows the two share links and the Sheet.
 *
 * Each run makes a new, separate set of forms and a new Sheet. If you rerun,
 * delete the old forms and Sheet from Google Drive so nobody gets old links.
 */

const BIGS = [
  'Big A',
  'Big B',
  'Big C',
];

const LITTLES = [
  'Little 1',
  'Little 2',
  'Little 3',
];

const TOP_N = 10;

function createForms() {
  const sheet = SpreadsheetApp.create('Big/Little rankings (responses)');
  writeRoster(sheet);
  const bigForm = makeForm('Bigs: rank your Littles', 'Which Big are you?', BIGS, LITTLES);
  const littleForm = makeForm('Littles: rank your Bigs', 'Which Little are you?', LITTLES, BIGS);
  bigForm.setDestination(FormApp.DestinationType.SPREADSHEET, sheet.getId());
  littleForm.setDestination(FormApp.DestinationType.SPREADSHEET, sheet.getId());

  Logger.log('Send to Bigs:      ' + bigForm.getPublishedUrl());
  Logger.log('Send to Littles:   ' + littleForm.getPublishedUrl());
  Logger.log('Edit Bigs form:    ' + bigForm.getEditUrl());
  Logger.log('Edit Littles form: ' + littleForm.getEditUrl());
  Logger.log('Responses Sheet:   ' + sheet.getUrl());
}

function makeForm(title, nameQuestion, ownSide, otherSide) {
  const form = FormApp.create(title);
  form.setDescription(
      'Pick up to ' + TOP_N + ' people in order, starting with your top choice. ' +
      'Only list people you would actually be happy with, and leave the rest blank. ' +
      "Don't pick the same person twice. " +
      'Your answers are private. You can come back and edit until submissions close.');
  form.setCollectEmail(true);
  form.setLimitOneResponsePerUser(true);  // requires a Google sign-in
  form.setAllowResponseEdits(true);
  form.setShowLinkToRespondAgain(false);
  form.setPublishingSummary(false);

  form.addListItem()
      .setTitle(nameQuestion)
      .setChoiceValues(ownSide)
      .setRequired(true);

  const names = otherSide.slice().sort();
  const ordinals = ['1st', '2nd', '3rd'];
  for (let i = 1; i <= TOP_N; i++) {
    form.addListItem()
        .setTitle((ordinals[i - 1] || i + 'th') + ' choice')
        .setChoiceValues(names)
        .setRequired(i === 1);
  }
  return form;
}

// "Roster" tab with everyone's name, so the converter can tell who hasn't
// submitted yet. Download it as CSV along with the two response tabs.
function writeRoster(sheet) {
  const tab = sheet.getSheets()[0].setName('Roster');
  const rows = [['Bigs', 'Littles']];
  for (let i = 0; i < Math.max(BIGS.length, LITTLES.length); i++) {
    rows.push([BIGS[i] || '', LITTLES[i] || '']);
  }
  tab.getRange(1, 1, rows.length, 2).setValues(rows);
}
