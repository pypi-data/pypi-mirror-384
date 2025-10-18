import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { ICommandPalette } from '@jupyterlab/apputils';
import { INotebookTracker, NotebookPanel } from '@jupyterlab/notebook';
import { CodeCell } from '@jupyterlab/cells';
import { ContentsManager } from '@jupyterlab/services';
import { Contents } from '@jupyterlab/services';
import { PageConfig } from '@jupyterlab/coreutils';
import { showDialog, Dialog } from '@jupyterlab/apputils';
import { Widget } from '@lumino/widgets';
import { ISettingRegistry } from '@jupyterlab/settingregistry';

//import { IObservableJSON } from '@jupyterlab/observables';

/**
 * Initialization data for the m269-25j-marking-tool extension.
 */
const prep_command = 'm269-25j-marking-tool:prep';
const colourise_command = 'm269-25j-marking-tool:colourise';
const prep_for_students = 'm269-25j-marking-tool:prep_for_students';
const al_tests_command = 'm269-25j-prep-al-tests';
const open_all_tmas = 'm269-25j-marking-tool:open_all_tmas';

// Initial code cell code pt 1
const initial_code_cell_pt1 = `import pickle
from IPython.display import display, Markdown, HTML
import ipywidgets as widgets  # Ensure ipywidgets is imported

# Dictionary to store marks
pickle_file = "marks.dat"
try:
    with open(pickle_file, "rb") as f:
        question_marks = pickle.load(f)
except FileNotFoundError:
    print('Data file does not exist')`;

// Initial code cell code pt 2
const initial_code_cell_pt2 = `def on_radio_change(change, question_id, radio_widget):
    """React to radio button changes."""
    print('Radio change')
    print(change)
    question_marks[question_id]["awarded"] = change["new"]
    with open("marks.dat", "wb") as f:  # "wb" = write binary mode
        pickle.dump(question_marks, f)

def generate_radio_buttons(question_id):
    """Create radio buttons linked to stored_answers, updating a Markdown cell."""
    if question_id not in question_marks:
        raise ValueError(f"Question {question_id} not found in dictionary")
    previous_selection = question_marks[question_id].get("awarded")

    # Create radio buttons
    radio_buttons = widgets.RadioButtons(
        options=[key for key in question_marks[question_id].keys() if key != "awarded"],
        description="Grade:",
        disabled=False
    )
    if previous_selection is not None:
        radio_buttons.value = previous_selection  # Restore previous selection
    else:
        radio_buttons.value = None  # Ensure no selection
    # Attach event listener
    radio_buttons.observe(lambda change: on_radio_change(change, question_id,
    radio_buttons), names='value')

    # Display the radio buttons
    display(radio_buttons)


def create_summary_table():
    """Generate and display an HTML table from the question_marks dictionary."""
    if not question_marks:
        display(HTML("<p>No data available.</p>"))
        return

    # Start the HTML table with styling
    html = """
    <style>
        table {
            border-collapse: collapse;
            width: 100%;
            text-align: center;
        }
        th, td {
            border: 1px solid black;
            padding: 8px;
        }
        .not-selected {
            background-color: #ffcccc;
        }
    </style>
    <table>
        <tr>
            <th>Question</th>
            <th>Fail</th>
            <th>Pass</th>
            <th>Merit</th>
            <th>Distinction</th>
            <th>Awarded</th>
            <th>Marks</th>
        </tr>
    """

    total_marks = 0  # Sum of all selected marks

    # Loop through the dictionary to populate rows
    for question, values in question_marks.items():
        fail = values.get("fail", "-")
        passed = values.get("pass", "-")
        merit = values.get("merit", "-")
        distinction = values.get("distinction", "-")
        awarded = values.get("awarded", None)

        # If marked is None, highlight the cell
        awarded_display = awarded if awarded else "Not Awarded"
        awarded_class = "not-selected" if awarded is None else ""

        if awarded is not None:
            total_marks += values[awarded]  # Add to total
            marks = values[awarded]
        else:
            marks = 0

        html += f"""
        <tr>
            <td>{question}</td>
            <td>{fail}</td>
            <td>{passed}</td>
            <td>{merit}</td>
            <td>{distinction}</td>
            <td class='{awarded_class}'>{awarded_display}</td>
            <td>{marks}</td>
        </tr>
        """

    # Add total row
    html += f"""
    <tr>
        <td colspan='6'><b>Total Marks</b></td>
        <td><b>{total_marks}</b></td>
    </tr>
    """

    html += "</table>"
    # Display the table in the Jupyter Notebook
    display(HTML(html))`;

// Question Marks JSON
// TMA 01
const question_marks_tma01 = `    question_marks = {
        "Q1a": {"fail": 0, "pass": 2, "awarded": None},
        "Q1b": {"fail": 0, "pass": 2, "awarded": None},
        "Q1c": {"fail": 0, "pass": 2, "awarded": None},
        "Q2a": {"fail": 0, "pass": 3, "merit": 6, "distinction": 8, "awarded": None},
        "Q2bi": {"fail": 0, "pass": 5, "merit": 9, "distinction": 13, "awarded": None},
        "Q2bii": {"fail": 0, "pass": 2, "awarded": None},
        "Q2c": {"fail": 0, "pass": 3, "merit": 6, "distinction": 8, "awarded": None},
        "Q2d": {"fail": 0, "pass": 2, "merit": 3, "distinction": 5, "awarded": None},
        "Q3a": {"fail": 0, "pass": 4, "merit": 7, "distinction": 10, "awarded": None},
        "Q3b": {"fail": 0, "pass": 2, "awarded": None},
        "Q4a": {"fail": 0, "pass": 2, "merit": 4, "distinction": 6, "awarded": None},
        "Q4b": {"fail": 0, "pass": 2, "merit": 4, "awarded": None},
        "Q5a": {"fail": 0, "pass": 2, "merit": 4, "distinction": 6, "awarded": None},
        "Q5b": {"fail": 0, "pass": 3, "merit": 5, "distinction": 8, "awarded": None},
        "Q5c": {"fail": 0, "pass": 2, "merit": 4, "distinction": 6, "awarded": None},
        "Q6a": {"fail": 0, "pass": 4, "merit": 7, "distinction": 10, "awarded": None},
        "Q6b": {"fail": 0, "pass": 3, "merit": 6, "awarded": None},
    }`;
// TMA 02
const question_marks_tma02 = `    question_marks = {
        "Q1a": {"fail": 0, "pass": 2, "awarded": None},
        "Q1b": {"fail": 0, "pass": 2, "awarded": None},
        "Q1c": {"fail": 0, "pass": 2, "awarded": None},
        "Q2a": {"fail": 0, "pass": 3, "merit": 6, "distinction": 9, "awarded": None},
        "Q2b": {"fail": 0, "pass": 2, "merit": 4, "distinction": 6, "awarded": None},
        "Q2c": {"fail": 0, "pass": 2, "merit": 4, "distinction": 6, "awarded": None},
        "Q3a": {"fail": 0, "pass": 2, "merit": 4, "distinction": 6, "awarded": None},
        "Q3bi": {"fail": 0, "pass": 1, "merit": 3, "awarded": None},
        "Q3bii": {"fail": 0, "pass": 2, "merit": 4, "awarded": None},
        "Q4a": {"fail": 0, "pass": 2, "merit": 4, "distinction": 5, "awarded": None},
        "Q4bi": {"fail": 0, "pass": 1, "merit": 2, "distinction": 3, "awarded": None},
        "Q4bii": {"fail": 0, "pass": 1, "merit": 2, "awarded": None},
        "Q4biii": {"fail": 0, "pass": 6, "merit": 10, "distinction": 14,
         "awarded": None},
        "Q5a": {"fail": 0, "pass": 1, "merit": 2, "awarded": None},
        "Q5b": {"fail": 0, "pass": 1, "merit": 2, "awarded": None},
        "Q5c": {"fail": 0, "pass": 1, "merit": 2, "awarded": None},
        "Q5d": {"fail": 0, "pass": 1, "merit": 2, "awarded": None},
        "Q5e": {"fail": 0, "pass": 1, "merit": 2, "awarded": None},
        "Q5f": {"fail": 0, "pass": 1, "merit": 2, "awarded": None},
        "Q6a": {"fail": 0, "pass": 7, "merit": 12, "distinction": 16, "awarded": None},
        "Q6b": {"fail": 0, "pass": 2, "merit": 3, "distinction": 4, "awarded": None},
        "Q6c": {"fail": 0, "pass": 2, "merit": 4, "awarded": None},
    }`
// TMA 03
const question_marks_tma03 = `    question_marks = {
        "Q1a": {"fail": 0, "pass": 3, "merit": 5, "distinction": 7, "awarded": None},
        "Q1b": {"fail": 0, "pass": 3, "distinction": 6, "awarded": None},
        "Q1c": {"fail": 0, "pass": 2, "distinction": 5, "awarded": None},
        "Q1d": {"fail": 0, "pass": 2, "merit": 4, "distinction": 6, "awarded": None},
        "Q1e": {"fail": 0, "pass": 2, "merit": 4, "distinction": 6, "awarded": None},
        "Q2a": {"fail": 0, "pass": 2, "distinction": 4, "awarded": None},
        "Q2b": {"fail": 0, "pass": 3, "distinction": 6, "awarded": None},
        "Q2c": {"fail": 0, "pass": 4, "merit": 7, "distinction": 10, "awarded": None},
        "Q2d": {"fail": 0, "pass": 2, "merit": 3, "distinction": 4, "awarded": None},
        "Q2e": {"fail": 0, "pass": 2, "merit": 4, "distinction": 6, "awarded": None},
        "Q3a": {"fail": 0, "pass": 3, "awarded": None},
        "Q3b": {"fail": 0, "pass": 2, "merit": 4, "distinction": 6, "awarded": None},
        "Q4a": {"fail": 0, "pass": 2, "merit": 3, "distinction": 4, "awarded": None},
        "Q4b": {"fail": 0, "pass": 3, "merit": 6, "distinction": 8, "awarded": None},
        "Q4c": {"fail": 0, "pass": 3, "merit": 6, "distinction": 8, "awarded": None},
        "Q4d": {"fail": 0, "pass": 3, "merit": 6, "distinction": 8, "awarded": None},
        "Q5" : {"fail": 0, "pass": 3, "awarded": None},
    }`;

// Testing calls
const testCalls: Record<number, Record<string, string>> = {
  1: {
    'Q2bi' : `try: # allowed
    test(find_client_surname, al_test_table_tma01_q2bi)
except NameError:
    print('Function not defined.')`,
    'Q3a'  : `try: # allowed
    test(find_occurrences_with_follow_on, al_test_table_tma01_q3a)
except NameError:
    print('Function not defined.')`,
    'Q4a'  : `al_tests_tma01_q4a()`,
    'Q5b'  : `try: # allowed
    test(council_decision, al_test_table_tma01_q5b)
except NameError:
    print('Function not defined.')`,
    'Q6a'  : `try: # allowed
    test(weighted_council_decision, al_test_table_tma01_q6a)
except NameError:
    print('Function not defined.')`
  },
  2: {
    'Q2a'  : 'test(power, al_test_table_tma02_q2a)',
    'Q4biii' : 'al_test_tma02_q4biii()',
    'Q6a'  : 'al_test_tma02_q6a()'
  },
  3: {
    'Q1a'  : 'al_test_tma03_q1a()',
    'Q1d'  : 'al_test_tma03_q1d()',
    'Q2d'  : 'al_test_tma03_q2d()',
    'Q4d'  : 'al_tests_tma03_q4d()'
  }
};

// Walk through root dir looking for files
async function walkDir(
  contents: Contents.IManager,
  path: string,
  collected: string[] = []
): Promise<string[]> {
  const listing = await contents.get(path, { content: true });

  if (listing.type === 'directory' && listing.content) {
    for (const item of listing.content) {
      if (item.type === 'directory') {
        await walkDir(contents, item.path, collected);
      } else if (item.type === 'notebook' && item.path.endsWith('.ipynb')) {
        collected.push(item.path);
      }
    }
  }
  return collected;
}

export async function decrypt(): Promise<string> {
  // Replace this with your encrypted base64-encoded string
  const ENCRYPTED_BASE64 = "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";
  const keyText = prompt("Enter 16-character decryption key:");
  if (!keyText || keyText.length !== 16) {
    throw new Error("Invalid key. Must be exactly 16 characters.");
  }

  const encryptedBytes = Uint8Array.from(atob(ENCRYPTED_BASE64), c => c.charCodeAt(0));
  const iv = encryptedBytes.slice(0, 12);
  const ciphertext = encryptedBytes.slice(12);

  const encoder = new TextEncoder();
  const keyData = encoder.encode(keyText);
  const key = await crypto.subtle.importKey(
    "raw",
    keyData,
    { name: "AES-GCM" },
    false,
    ["decrypt"]
  );

  const decryptedBuffer = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv },
    key,
    ciphertext
  );

  return new TextDecoder().decode(decryptedBuffer);
}

function getSetting(settings: ISettingRegistry.ISettings, key: string, default_value: string): string {
  try {
    const value = settings.get(key).composite;
    return typeof value === 'string' ? value : '';
  } catch (err) {
    console.warn(`Error reading setting "${key}":`, err);
    return default_value;
  }
}

const plugin: JupyterFrontEndPlugin<void> = {
  id: 'm269-25j-marking-tool:plugin',
  description: 'A tutor marking tool for M269 in the 25J presentation',
  autoStart: true,
  requires: [ICommandPalette, INotebookTracker, ISettingRegistry],
  activate: async (
    app: JupyterFrontEnd, 
    palette: ICommandPalette, 
    notebookTracker: INotebookTracker, 
    settingRegistry: ISettingRegistry
  ) => {
    console.log('JupyterLab extension m269-25j-marking-tool is activated! hurrah');
    console.log('Loading settings registry');
    const settings = await settingRegistry.load('m269-25j-marking-tool:plugin');
    console.log('Loading colours');
    const answer_colour = getSetting(settings,'answer_colour','rgb(255, 255, 204)');
    const feedback_colour = getSetting(settings,'feedback_colour','rgb(93, 163, 243)');
    const tutor_colour = getSetting(settings,'tutor_colour','rgb(249, 142, 142)');
    console.log('Answers: '+answer_colour);
    console.log('Feedback: '+feedback_colour);
    console.log('Tutor: '+tutor_colour);
    // Inject custom styles
    const style = document.createElement('style');
    /*style.textContent = `
      .m269-answer {
        background-color:rgb(255, 255, 204) !important;
      }
      .m269-feedback {
        background-color:rgb(93, 163, 243) !important;
      }
      .m269-tutor {
        background-color: rgb(249, 142, 142) !important;
      }
    `;*/
    style.textContent = `
      .m269-answer {
        background-color:`+answer_colour+` !important;
      }
      .m269-feedback {
        background-color:`+feedback_colour+` !important;
      }
      .m269-tutor {
        background-color: `+tutor_colour+` !important;
      }
    `;
    document.head.appendChild(style);

    // Prep command
    app.commands.addCommand(prep_command, {
      label: 'M269 Prep for Marking',
      caption: 'M269 Prep for Marking',
      execute: async (args: any) => {
        const currentWidget = app.shell.currentWidget;
        if (currentWidget instanceof NotebookPanel) {
          const notebook = currentWidget.content;
          const metadata = currentWidget?.context?.model?.metadata;
          console.log('metadata');
          console.log(metadata);
          console.log(metadata["TMANUMBER"]);
          if (!metadata) {
            console.error('Notebook metadata is undefined');
            return;
          }
          if (metadata["TMANUMBER"] != 1 && metadata["TMANUMBER"] != 2 && metadata["TMANUMBER"] != 3) {
            alert("Could not identify TMA number.");
            return;
          }
          if (metadata["TMAPRES"] != "25J") {
            alert("This tool is only for presentation 25J. This TMA not identifiable as a 25J assessment.");
            return;
          }
          // Duplicate the file
          const oldName = currentWidget.context.path;
          const newName = oldName.replace(/\.ipynb$/, '-UNMARKED.ipynb');
          await app.serviceManager.contents.copy(oldName, newName);
          console.log('Notebook copied successfully:', newName);
          // Insert initial code cell
          notebook.activeCellIndex = 0;
          notebook.activate();
          await app.commands.execute('notebook:insert-cell-above');
          const cell = notebook.activeCell;
          console.log("Getting TMA number");
          if (cell && cell.model.type === 'code') {
            let question_marks = "";
            if (metadata["TMANUMBER"] == 1) {
              question_marks = question_marks_tma01;
            } else if (metadata["TMANUMBER"] == 2) {
              question_marks = question_marks_tma02;
            } else if (metadata["TMANUMBER"] == 3) {
              question_marks = question_marks_tma03;
            } else {
              alert("TMA Not identified from metadata");
              return;
            }
            (cell as CodeCell).model.sharedModel.setSource(`${initial_code_cell_pt1}\n\n${question_marks}\n\n${initial_code_cell_pt2}`);
            cell.model.setMetadata('CELLTYPE','MARKCODE');
            await app.commands.execute('notebook:run-cell');
            if (cell) {
              cell.inputHidden = true;
            }
          }
          console.log("inserting marking forms");
          // Insert marking cell after every cell with metadata "QUESTION"
          for (let i = 0; i < notebook.widgets.length; i++) {
            console.log(i);
            const currentCell = notebook.widgets[i];
            const meta = currentCell.model.metadata as any;
            const celltype = meta['CELLTYPE'];
            console.log(celltype);
            const questionValue = meta['QUESTION'];
            console.log(questionValue);
            if (celltype == 'TMACODE') {
              notebook.activeCellIndex = i;
              await app.commands.execute('notebook:run-cell');
            }
            if (questionValue !== undefined) {
              notebook.activeCellIndex = i;
              await app.commands.execute('notebook:insert-cell-below');
              let insertedCell = notebook.activeCell;
              if (insertedCell && insertedCell.model.type === 'code') {
                (insertedCell as CodeCell).model.sharedModel.setSource(`# Marking Form
generate_radio_buttons(${JSON.stringify(questionValue)})`);
                insertedCell.model.setMetadata('CELLTYPE','MARKCODE');
              }
              await app.commands.execute('notebook:run-cell');
              i++; // Skip over inserted cell to avoid infinite loop
              
              notebook.activeCellIndex = i;
              await app.commands.execute('notebook:insert-cell-below');
              await app.commands.execute('notebook:change-cell-to-markdown');
              insertedCell = notebook.activeCell;
              if (insertedCell && insertedCell.model.type === 'markdown') {
                console.log('markdown cell being metadatad');
                (insertedCell as CodeCell).model.sharedModel.setSource(`Feedback:`);
                insertedCell.model.setMetadata('CELLTYPE','FEEDBACK');
              } else {
                console.log('markdown cell cannot be metadatad');
              }
              await app.commands.execute('notebook:run-cell');
              i++; // Skip over inserted cell to avoid infinite loop
            }
          }
          // Insert final code cell at bottom
          //await app.commands.execute('notebook:activate-next-cell');
          notebook.activeCellIndex = notebook.widgets.length -1;

          console.log('Inserting final cell');
          await app.commands.execute('notebook:insert-cell-below');
          console.log('Getting final cell');
          const finalCell = notebook.widgets[notebook.widgets.length - 1];
          console.log(finalCell);
          if (finalCell) {
            console.log('Got final cell');
            console.log(finalCell.model.type);
          } else {
            console.log('Not got final cell');
          }
          if (finalCell && finalCell.model.type === 'code') {
            console.log('got and it is code');
            (finalCell as CodeCell).model.sharedModel.setSource(`create_summary_table()`);
            finalCell.model.setMetadata('CELLTYPE','MARKCODE');

          } else {
            console.log('could not get or not code');
          }
          console.log('activating');
          await app.commands.execute('notebook:run-cell');
          // Automatically run the colourise command after prep
          await app.commands.execute(colourise_command);
          console.log('done');
        }
      }
    });
    // End prep command

    // Colourise command
    app.commands.addCommand(colourise_command, {
      label: 'M269 Colourise',
      caption: 'M269 Colourise',
      execute: async (args: any) => {
        const currentWidget = app.shell.currentWidget;
        if (currentWidget instanceof NotebookPanel) {
          const notebook = currentWidget.content;
          console.log('Colourising cells');
          for (let i = 0; i < notebook.widgets.length; i++) {
            console.log(i);
            const currentCell = notebook.widgets[i];
            const meta = currentCell.model.metadata as any;
            const celltype = meta['CELLTYPE'];
            console.log(celltype);
            if (celltype === 'ANSWER') {
              currentCell.addClass('m269-answer');
            } else if (celltype === "FEEDBACK") {
              currentCell.addClass('m269-feedback');
            } else if (celltype === "MARKCODE") {
              currentCell.addClass('m269-feedback');              
            } else if (celltype === "SOLUTION" || celltype === "SECREF" || celltype === "GRADING") {
              currentCell.addClass('m269-tutor');
            }
          }
        }
      }
    });
    // End colourise command

    // Prep-for-students command
    app.commands.addCommand(prep_for_students, {
      label: 'M269 Prep for Student (MT)',
      caption: 'M269 Prep for Student (MT)',
      execute: async (args: any) => {
        const currentWidget = app.shell.currentWidget;
        if (currentWidget instanceof NotebookPanel) {
          // Duplicate the file
          const oldName = currentWidget.context.path;
          const masterName = oldName;
          //const newName = oldName.replace(/-Master(?=\.ipynb$)/, "");
          const newName = oldName
            .replace(/-Master(?=\.ipynb$)/, "")
            .replace(/(?=\.ipynb$)/, "-STUDENT");

          await currentWidget.context.save();

          await app.serviceManager.contents.rename(oldName, newName);

          await currentWidget.close();
          
          const newWidget = await app.commands.execute('docmanager:open', {
            path: newName,
            factory: 'Notebook'
          });

          if (newWidget && 'context' in newWidget) {
            await (newWidget as NotebookPanel).context.ready;
          }
          
          await app.serviceManager.contents.copy(newName, masterName);
          
          console.log('Notebook copied successfully:', newName);
          // Iterate backwards over the cells
          const notebook = newWidget.content;
          for (let i = notebook.widgets.length - 1; i >= 0; i--) {
            const cell = notebook.widgets[i];
            const meta = cell.model.metadata as any;
            const celltype = meta['CELLTYPE'];
            // Do something with each cell
            console.log(`Cell ${i} type: ${cell.model.type} - ${celltype}`);
            if (celltype == 'SECREF' || celltype == 'SOLUTION' || celltype == 'GRADING') {
              notebook.activeCellIndex = i;
              await app.commands.execute('notebook:delete-cell');
              console.log('... deleted.');
            }
          }
        }
      }
    });

    async function ensurePopupsAllowed(): Promise<boolean> {
      // 1) Try to open a harmless placeholder immediately (sync).
      // If it returns null, the browser blocked it.
      const testWin = window.open('about:blank', '_blank');

      if (!testWin) {
        // 2) Build site/origin string for instructions
        //const baseUrl = PageConfig.getBaseUrl();          // e.g. "/user/olih/lab"
        const origin  = window.location.origin;           // e.g. "https://yourhub.example.org"
        //const site    = `${origin}${baseUrl}`.replace(/\/lab\/?$/, ''); // hub root-ish

        const body = document.createElement('div');
        body.innerHTML = `
          <p><b>Pop-ups are blocked</b> for <code>${origin}</code>. To open multiple notebooks automatically, please allow pop-ups for this site, then click <b>Try again</b>.</p>
          <details open>
            <summary><b>How to allow pop-ups</b></summary>
            <ul style="margin-top:0.5em">
              <li><b>Check your address bar:</b> There may be an option to whitelist popups.</li>
              <li><b>Chrome / Edge (Chromium):</b> Click the icon to left of address bar → <i>Site settings</i> → set <i>Pop-ups and redirects</i> to <b>Allow</b> for <code>${origin}</code>. Then close the tab to return.</li>
              <li><b>Firefox:</b> Preferences → <i>Privacy &amp; Security</i> → <i>Permissions</i> → uncheck <i>Block pop-up windows</i> or add an exception for <code>${origin}</code>.</li>
              <li><b>Safari (macOS):</b> Safari → Settings → <i>Websites</i> → <i>Pop-up Windows</i> → for <code>${origin}</code>, choose <b>Allow</b>. Or “Settings for This Website…” from the address bar.</li>
            </ul>
          </details>
          <p style="margin-top:0.5em">Tip: some extensions (ad blockers, privacy tools) also block pop-ups; whitelist this site there if needed.</p>
        `;
        const bodyWidget = new Widget({ node: body });

        const result = await showDialog({
          title: 'Allow pop-ups to open notebooks',
          body: bodyWidget,
          //buttons: [Dialog.cancelButton({ label: 'Cancel' }), Dialog.okButton({ label: 'Try again' })]
          buttons: [Dialog.cancelButton({ label: 'Cancel' })]
        });

        return result.button.accept;
      } else {
        // 3) We had permission—tidy up and continue
        try { testWin.close(); } catch { /* ignore */ }
        return true;
      }
    }

    // Prepare the AL tests command
    app.commands.addCommand(al_tests_command, {
      label: 'M269 AL Tests',
      caption: 'M269 AL Tests',
      
      execute: async (args: any) => {
        const contents = new ContentsManager();
        const currentWidget = notebookTracker.currentWidget;
        if (currentWidget) {
          const notebookPath = currentWidget.context.path; // e.g. "subdir/notebook.ipynb"
          console.log("Notebook path:", notebookPath);
        }
        const notebookPath = currentWidget?.context.path ?? ""
        const upLevels = notebookPath.split("/").length - 1;
        const relPathToRoot = Array(upLevels).fill("..").join("/");
        const fullPath = relPathToRoot ? `${relPathToRoot}/al_tests.py` : "al_tests.py";
        let fileContent: string;
        try {
          fileContent = await decrypt();
        } catch (err) {
          alert("Decryption failed: " + (err instanceof Error ? err.message : err));
          return;
        }
        //alert('here');
        const filePath = 'al_tests.py';  // This is in the root folder
        try {
          await contents.save(filePath, {
            type: 'file',
            format: 'text',
            content: fileContent
          });
          console.log('File created successfully');
          if (currentWidget instanceof NotebookPanel) {
            // 1. Put run call in cell 0
            const notebook = currentWidget.content;
            notebook.activeCellIndex = 0;
            notebook.activate();
            await app.commands.execute('notebook:insert-cell-above');
            const cell = notebook.activeCell;
            const code = `%run -i ${fullPath}`;
            (cell as CodeCell).model.sharedModel.setSource(code);
            await app.commands.execute('notebook:run-cell');
            // 2. Check TMA number
            const metadata = currentWidget?.context?.model?.metadata;
            console.log('metadata');
            console.log(metadata);
            console.log(metadata["TMANUMBER"]);
            if (!metadata) {
              console.error('Notebook metadata is undefined');
              return;
            }
            if (metadata["TMANUMBER"] != 1 && metadata["TMANUMBER"] != 2 && metadata["TMANUMBER"] != 3) {
              alert("Could not identify TMA number.");
              return;
            }
            if (metadata["TMAPRES"] != "25J") {
              alert("This tool is only for presentation 25J. This TMA not identifiable as a 25J assessment.");
              return;
            }
            console.log('Identified as TMA '+metadata["TMANUMBER"]+' Presentation '+metadata["TMAPRES"]);
            // 3. Iterate over dictionary for relevant TMA puttin calls in CELLTYPE:ANSWER with relevant QUESTION at last line.
            const tmaNumber = metadata["TMANUMBER"];
            const entries = testCalls[tmaNumber];
            if (entries) {
              for (const [key, value] of Object.entries(entries)) {
                console.log(`Key: ${key}, Value: ${value}`);
                for (let i = 0; i < notebook.widgets.length; i++) {
                  const currentCell = notebook.widgets[i];
                  const meta = currentCell.model.metadata as any;
                  const questionKey = meta["QUESTION"];
                  const cellType = meta["CELLTYPE"];
                  console.log(`Cell ${i}: Type = ${cellType}, Question = ${questionKey}`);
                  if (cellType === "ANSWER" && questionKey === key && currentCell.model.type === "code") {
                    console.log('found');
                    let existing = (currentCell as CodeCell).model.sharedModel.getSource();
                    (currentCell as CodeCell).model.sharedModel.setSource(existing + `\n\n`+value);
                  }
                  if (i == 18 || i == 19 || i == 20) {
                    console.log(cellType);
                    console.log(cellType === "ANSWER");
                    console.log(questionKey);
                    console.log(key)
                    console.log(questionKey === key);
                    console.log(currentCell.model.type)
                    console.log(currentCell.model.type === "code");
                  }
                }
              }
            }
            console.log(code);
          } else {
            alert('Error: Could not access NotebookPanel');
            return;
          }
        } catch (err) {
          alert('Failed to create file: '+ err);
          return;
        }
      }
    });

    // Open all TMAs
    app.commands.addCommand(open_all_tmas, {
            label: 'M269 Open All TMAs',
      caption: 'M269 Open All TMAs',
      
      execute: async (args: any) => {
        // Ask for popup permission (or instructions if blocked)
        const ok = await ensurePopupsAllowed();
        if (!ok) return; // user cancelled
        //alert('OK');
        const contents = app.serviceManager.contents;
        // 1) collect all notebooks from the Jupyter root
        let notebooks = await walkDir(contents, ''); // '' = root

        notebooks = notebooks.filter(path => !path.includes('-UNMARKED'));

        // DEBUG
        const baseUrl = PageConfig.getBaseUrl();
        console.log('OPEN ALL DEBUGGING START');
        for (const path of notebooks) {
          const url = baseUrl + 'lab/tree/' + encodeURIComponent(path);
          console.log('>> '+url);
        }
        console.log('OPEN ALL DEBUGGING END');


        // END DEBUG

        // (optional) sanity check so you don't open hundreds at once
        if (notebooks.length > 20) {
          const ok = window.confirm(
            `Found ${notebooks.length} notebooks. Open them all in new tabs?`
          );
          if (!ok) return;
        }
        
        // 2) open each notebook in a new browser tab
        //const baseUrl = PageConfig.getBaseUrl();
        for (const path of notebooks) {
          const url = baseUrl + 'lab/tree/' + encodeURIComponent(path);
          window.open(url, '_blank');
        }

        alert(`Opened ${notebooks.length} notebooks in new tabs.\mIf they didn't open, enable popups for this site and try again.`);   
      }
    });

    const category = 'M269-25j';
    // Add commands to pallette
    palette.addItem({ command: prep_command, category, args: { origin: 'from palette' } });
    palette.addItem({ command: colourise_command, category, args: { origin: 'from palette' } });
    palette.addItem({ command: prep_for_students, category, args: { origin: 'from palette' } });
    palette.addItem({ command: al_tests_command, category, args: {origin: 'from palette' }});
    palette.addItem({ command: open_all_tmas, category, args: {origin: 'from palette' }});
  }
};

export default plugin;
