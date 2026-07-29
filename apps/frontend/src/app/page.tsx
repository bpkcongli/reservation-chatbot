import ChatWidget from "@/domain/conversation/features/ChatWidget";
import LandingPage from "@/domain/landing/features/LandingPage";

export default function Home() {
  return (
    <>
      <LandingPage />
      <ChatWidget />
    </>
  );
}
