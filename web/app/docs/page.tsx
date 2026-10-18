import { DocsView } from "@/components/docs-view";
import { Assistant } from "@/components/assistant";
import { SiteHeader } from "@/components/site-header";

export default function DocsPage() {
  return (
    <>
      <SiteHeader />
      <DocsView />
      <Assistant />
    </>
  );
}
