import ReactMarkdown from "react-markdown";

interface Props {
  content: string;
}

export function MarkdownMessage({ content }: Props) {
  return (
    <div className="markdown-body">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}
