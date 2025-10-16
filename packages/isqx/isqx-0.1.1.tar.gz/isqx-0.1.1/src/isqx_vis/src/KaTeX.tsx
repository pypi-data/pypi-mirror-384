import type { Component } from "solid-js";
import { createEffect } from "solid-js";
import katex from "katex";
import "katex/dist/katex.min.css";
import "katex/dist/contrib/copy-tex.js";

const KaTeX: Component<{ text: string; display?: boolean }> = props => {
  let spanRef: HTMLSpanElement | undefined;
  createEffect(() => {
    if (!spanRef) return;
    katex.render(props.text, spanRef, {
      throwOnError: false,
      displayMode: !!props.display
    });
  });
  return <span ref={spanRef} />;
};

export default KaTeX;
