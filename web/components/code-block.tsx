export function CodeBlock({ code, label }: { code: string; label?: string }) {
  return (
    <figure className="codeblock">
      {label ? <figcaption className="codeblock-head">{label}</figcaption> : null}
      <pre>
        <code>{code}</code>
      </pre>
    </figure>
  );
}
