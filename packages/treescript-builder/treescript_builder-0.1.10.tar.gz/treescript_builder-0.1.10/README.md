# TreeScript FileTreeBuilder
Script for Building File Trees.
 - Makes your dreams come true.

## How To Make The Most Of TreeScript
1. Think in File Trees:
   - Initial and Final Trees.
   - Tree Templates for New Modules, Packages, Apps.
   - Data Directory and Data Labels.
2. Prepare Your TreeScript Designs.
   - New Project in any language you want.
   - New Feature in a New Module File Tree.
3. Plan TreeScript Operations.
   - Split Larger Trees into multiple TreeScript Files.
   - Combine Trim and Build Operations in a Sequence to meet Workflow requirements.
   - Apply other TreeScript Packages to your Workflow:
     - [TreeScript-Diff] : Difference between two TreeScript files.
     - [TreeScript-Files] : Convert TreeScript into a list of File Paths.
     - [TreeScriptify] : Create TreeScript from existing File Trees.
4. Run TreeScript, as part of your Workflow.
   - Install; add aliases to your terminal config file, if desired.

## Script Structure
 - Directory names contain a slash char.
 - The Indentation is 2 spaces per level.

### Directory Slash Chars
 - Both directions are accepted: `\`, `/`
 - Start or End of the Directory Name: `\src` or `src/`
 - No spaces between Name and char.

### Example

```treescript
src/
  __init__.py
  dir/
```

# Project Technical Details

## File Tree Builder
Execute the File Tree Builder with the `ftb` command.
- Creates Files and Directories
- If DataLabels are present, a DataDirectory is required.

## File Tree Trimmer (Remover)
Execute the File Tree Remover by adding the `--trim` argument.
- Removes Files and Empty Directories.
- DataLabels require DataDirectory.
  - Files are exported to the DataDirectory. 

### Builder DataLabel
A `DataLabel` is a link to Text content to be inserted into the file.
 - DataLabel must be present in the DataDirectory, if present in the TreeScript File.
 - DataDirectory contents are checked during the Tree Validation phase of program execution.

#### Valid DataLabels
The range of accepted DataLabel characters has been narrowed to reduce risk.
 - Letters: A - z
 - Numbers: 0 - 9
 - Punctuation: -_.

#### Invalid DataLabels
The dot directories are invalid.
 - Current Dir: .
 - Parent Dir: ..

## Default Input Reader
Before the Reader receives TreeScript, the input is filtered so comments and empty lines are not ever seen by the Reader.
The Default Input Reader processes one line at a time and calculates multiple file tree node properties that it stores in dataclass objects.

It calculates for each node:
- Name
- File or directory status
- Depth in tree
- (optional) DataArgument

### Input Data Argument
The Data Argument specifies what will be inserted into the file that is created. The Data Argument is provided in the Input File, immediately after the File Name (separated by a space). There are two types of Data Arguments:
- DataLabel
- InlineContent

## Tree Trim Data Directory Feature
The Remover provides an additional feature beyond the removal of files in the Tree. This feature enables Files to be saved to a Data Directory when they are removed. Rather than destroying the file data, it is moved to a new directory.

## To-Do Features 
 - Append/Prepend
 - Overwrite Prevention
 - Inline Content

### Builder File Inline Content (TODO)
`Inline Content` is written in the Tree Node Structure Input file itself. To distinguish `DataContent` from a `DataLabel`, the Content must begin with a special character.

Options for the DataContent character are under consideration.
- Less than bracket is a good option: < 
- Star char is an alternative: *

This feature is a neat mid-sized improvement that may open up opportunities for more workflow flexibility.
 - Adding a new file late in the process.
   - such as after data directory is already prepared, and you review TS and notice a little thing missing.
   - value-adding option that helps you build files faster, more convenient than the DataDirectory.
 - Workflows that use TreeScript:
   - Easier To Plan, and Communicate What You Did.
   - Package Restructuring, Migrations.
   - Test Environment Setup
   - FileSystem Inventory