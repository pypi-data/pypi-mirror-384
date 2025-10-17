// This file is part of InvenioRDM
// Copyright (C) 2025 TU Wien.
//
// Invenio Theme TUW is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import React from "react";
import ReactDOM from "react-dom";
import { Editor } from "@tinymce/tinymce-react";

const config = {
  branding: false,
  menubar: false,
  statusbar: false,
  min_height: 200,
  content_style: "body { font-size: 14px; }",
  plugins: ["codesample", "link", "lists", "table", "autoresize", "wordcount"],
  contextmenu: false,
  toolbar:
    "blocks | bold italic link codesample blockquote table | bullist numlist | outdent indent | wordcount | undo redo",
  autoresize_bottom_margin: 20,
  block_formats: "Paragraph=p; Header 1=h1; Header 2=h2; Header 3=h3",
  table_advtab: false,
  convert_urls: false,
};

ReactDOM.render(
  <Editor
    id="html-msg"
    textareaName="html-msg"
    initialValue={document.getElementById("html-msg").value}
    init={config}
  />,
  document.getElementById("html-msg-container"),
);
