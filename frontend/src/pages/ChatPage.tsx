import React, { useState, useEffect, useRef } from 'react';
import {
  MessageSquare,
  Plus,
  Send,
  Trash2,
  FileText,
  Bookmark,
  ShieldCheck,
  AlertCircle,
  X,
  ExternalLink,
  Scale,
  Sparkles,
  ArrowRight
} from 'lucide-react';
import {
  Conversation,
  Message,
  Citation,
  createConversation,
  listConversations,
  getConversation,
  deleteConversation,
  sendMessage
} from '../services/api';
import { AiProcessingDetails } from '../components/chat/AiProcessingDetails';
import { ErrorBoundary } from '../components/common/ErrorBoundary';

export const ChatPage: React.FC = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputContent, setInputContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    if (activeConvId) {
      loadMessages(activeConvId);
    } else {
      setMessages([]);
    }
  }, [activeConvId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSending]);

  const extractErrorMessage = (err: any, fallback: string): string => {
    if (err?.response?.status === 401) {
      return 'Session expired or authentication required. Please sign in again.';
    }
    if (err?.response?.status === 403) {
      return 'You are not authorized to perform this operation.';
    }
    if (err?.response?.status === 429) {
      return 'AI rate limit reached. Please wait a moment before trying again.';
    }
    if (err?.response?.status === 503) {
      return 'AI service is temporarily unavailable. Please retry shortly.';
    }
    if (!err?.response && (err?.message === 'Network Error' || err?.code === 'ERR_NETWORK')) {
      return 'Unable to reach backend server. Please check your network connection.';
    }
    return (
      err?.response?.data?.detail ||
      err?.response?.data?.error?.message ||
      err?.message ||
      fallback
    );
  };

  const loadConversations = async () => {
    try {
      setIsLoading(true);
      const list = await listConversations();
      setConversations(list);
      if (list.length > 0 && !activeConvId) {
        setActiveConvId(list[0].id);
      }
    } catch (err) {
      setErrorMsg(extractErrorMessage(err, 'Failed to load research sessions.'));
    } finally {
      setIsLoading(false);
    }
  };

  const loadMessages = async (convId: string) => {
    try {
      const detail = await getConversation(convId);
      setMessages(detail.messages || []);
    } catch (err) {
      setErrorMsg(extractErrorMessage(err, 'Failed to load message history.'));
    }
  };

  const handleCreateNew = async () => {
    try {
      setErrorMsg(null);
      const newConv = await createConversation(`Legal Research (${new Date().toLocaleDateString()})`);
      setConversations((prev) => [newConv, ...prev]);
      setActiveConvId(newConv.id);
      setMessages([]);
    } catch (err) {
      setErrorMsg(extractErrorMessage(err, 'Failed to create new research session.'));
    }
  };

  const handleDeleteConversation = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (!window.confirm('Delete this conversation? All messages and citations will be removed.')) {
      return;
    }
    try {
      await deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (activeConvId === id) {
        const remaining = conversations.filter((c) => c.id !== id);
        setActiveConvId(remaining.length > 0 ? remaining[0].id : null);
      }
    } catch (err) {
      setErrorMsg(extractErrorMessage(err, 'Failed to delete conversation.'));
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const text = textToSend || inputContent;
    if (!text.trim() || isSending) return;

    let targetConvId = activeConvId;

    if (!targetConvId) {
      try {
        const newConv = await createConversation('Legal Research');
        setConversations((prev) => [newConv, ...prev]);
        setActiveConvId(newConv.id);
        targetConvId = newConv.id;
      } catch (err) {
        setErrorMsg(extractErrorMessage(err, 'Failed to initialize conversation.'));
        return;
      }
    }

    const optimisticUserMsg: Message = {
      id: `temp-${Date.now()}`,
      conversation_id: targetConvId,
      role: 'user',
      content: text,
      citations: [],
      claims: [],
      created_at: new Date().toISOString()
    };

    setMessages((prev) => [...prev, optimisticUserMsg]);
    setInputContent('');
    setIsSending(true);
    setErrorMsg(null);

    try {
      const assistantMsg = await sendMessage(targetConvId, text);
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setErrorMsg(extractErrorMessage(err, 'Failed to synthesize grounded answer.'));
    } finally {
      setIsSending(false);
    }
  };

  const quickPrompts = [
    'What are the confidentiality and non-disclosure obligations?',
    'What is the governing law and dispute resolution mechanism?',
    'Summarize the conditions for early contract termination.',
    'Are there any indemnification liability caps defined?'
  ];

  return (
    <div className="flex h-[calc(100vh-8rem)] max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 gap-6">
      {/* Sidebar: Conversation List */}
      <div className="w-80 flex flex-col bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden shrink-0">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Scale className="h-5 w-5 text-indigo-600" aria-hidden="true" />
            <h1 className="font-bold text-slate-800 text-sm">Research Sessions</h1>
          </div>
          <button
            onClick={handleCreateNew}
            className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1.5 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 rounded-lg transition"
            title="New Research Session"
            aria-label="Create new research session"
          >
            <Plus className="h-3.5 w-3.5" aria-hidden="true" />
            New
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-1.5">
          {isLoading && (
            <div className="text-center py-8 text-xs text-slate-500">Loading sessions...</div>
          )}

          {!isLoading && conversations.length === 0 && (
            <div className="text-center py-10 px-4">
              <MessageSquare className="h-8 w-8 text-slate-300 mx-auto mb-2" aria-hidden="true" />
              <p className="text-xs text-slate-500 font-medium">No sessions yet</p>
              <p className="text-[11px] text-slate-500 mt-1">
                Start a new conversation to ask questions across your uploaded legal documents.
              </p>
            </div>
          )}

          {conversations.map((conv) => {
            const isActive = conv.id === activeConvId;
            return (
              <div
                key={conv.id}
                onClick={() => setActiveConvId(conv.id)}
                className={`group flex items-center justify-between p-3 rounded-lg text-xs cursor-pointer transition border ${
                  isActive
                    ? 'bg-indigo-50/70 border-indigo-200 text-indigo-900 font-semibold'
                    : 'border-transparent text-slate-700 hover:bg-slate-50 hover:border-slate-100'
                }`}
              >
                <div className="flex items-center gap-2.5 truncate">
                  <MessageSquare
                    className={`h-4 w-4 shrink-0 ${
                      isActive ? 'text-indigo-600' : 'text-slate-400'
                    }`}
                    aria-hidden="true"
                  />
                  <span className="truncate">{conv.title}</span>
                </div>
                <button
                  onClick={(e) => handleDeleteConversation(e, conv.id)}
                  className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-red-600 rounded transition"
                  title="Delete Session"
                  aria-label={`Delete conversation ${conv.title}`}
                >
                  <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                </button>
              </div>
            );
          })}
        </div>

        <div className="p-3 border-t border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-2 text-[11px] text-slate-500">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-700" aria-hidden="true" />
            <span>Strict Tenant Isolation & Sandboxing</span>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden relative">
        {/* Error Alert Banner */}
        {errorMsg && (
          <div className="bg-red-50 border-b border-red-200 px-4 py-2.5 flex items-center justify-between text-xs text-red-700">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0 text-red-500" aria-hidden="true" />
              <span>{errorMsg}</span>
            </div>
            <button
              onClick={() => setErrorMsg(null)}
              className="text-red-500 hover:text-red-700"
              aria-label="Dismiss error message"
            >
              <X className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        )}

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 && !isSending && (
            <div className="max-w-xl mx-auto text-center py-12">
              <div className="inline-flex p-3 rounded-2xl bg-indigo-50 text-indigo-600 mb-4">
                <Sparkles className="h-6 w-6" aria-hidden="true" />
              </div>
              <h2 className="text-lg font-bold text-slate-900 mb-2">
                Grounded Legal AI Workspace
              </h2>
              <p className="text-xs text-slate-500 mb-6 leading-relaxed">
                Pose legal questions regarding your contracts, statutes, and case law. Answers are
                derived strictly from evidentiary documents with claim-level citations.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-left">
                {quickPrompts.map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => handleSendMessage(prompt)}
                    className="p-3 text-xs bg-slate-50 hover:bg-indigo-50/50 border border-slate-200 hover:border-indigo-200 rounded-lg text-slate-700 hover:text-indigo-900 transition flex items-center justify-between group"
                  >
                    <span>{prompt}</span>
                    <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-indigo-600 shrink-0 ml-2" aria-hidden="true" />
                  </button>
                ))}
              </div>
            </div>
          )}

          <ErrorBoundary fallbackMessage="An error occurred while displaying message history. Click below to recover.">
            {messages.map((msg) => {
              const isUser = msg.role === 'user';
              return (
                <div
                  key={msg.id}
                  className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
                >
                  {!isUser && (
                    <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-600 to-violet-500 text-white flex items-center justify-center font-bold text-xs shrink-0 shadow-sm mt-0.5">
                      AI
                    </div>
                  )}

                  <div className={`max-w-2xl space-y-2.5 ${isUser ? 'items-end' : 'items-start'}`}>
                    {/* Message Bubble */}
                    <div
                      className={`p-4 rounded-2xl text-xs leading-relaxed shadow-sm ${
                        isUser
                          ? 'bg-indigo-600 text-white rounded-br-none'
                          : 'bg-slate-50 border border-slate-200 text-slate-800 rounded-bl-none'
                      }`}
                    >
                      <div className="whitespace-pre-wrap">{msg.content}</div>
                    </div>

                    {/* Assistant Citations & Claim Grounding */}
                    {!isUser && msg.citations && msg.citations.length > 0 && (
                      <div className="space-y-1.5 pt-1">
                        <div className="flex items-center gap-1 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                          <Bookmark className="h-3 w-3 text-indigo-500" aria-hidden="true" />
                          <span>Evidentiary Citations ({msg.citations.length})</span>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {msg.citations.map((cit) => (
                            <button
                              key={cit.id}
                              onClick={() => setSelectedCitation(cit)}
                              aria-label={`View citation ${cit.citation_order} from ${cit.document_title || 'Document'}, page ${cit.page_number}`}
                              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium bg-amber-50 text-amber-900 border border-amber-200/80 hover:bg-amber-100 transition shadow-2xs"
                            >
                              <span className="font-bold text-amber-800">[{cit.citation_order}]</span>
                              <span className="truncate max-w-[160px]">
                                {cit.document_title || 'Document'}
                              </span>
                              <span className="text-amber-800 font-semibold">p.{cit.page_number}</span>
                              <ExternalLink className="h-2.5 w-2.5 opacity-60 ml-0.5" aria-hidden="true" />
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {!isUser && msg.processing_details && (
                      <AiProcessingDetails
                        details={msg.processing_details}
                        modelName={msg.model_name}
                      />
                    )}
                  </div>

                  {isUser && (
                    <div className="w-8 h-8 rounded-full bg-slate-200 text-slate-600 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                      You
                    </div>
                  )}
                </div>
              );
            })}
          </ErrorBoundary>

          {/* Typing indicator */}
          {isSending && (
            <div className="flex gap-3 justify-start items-center">
              <div className="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-xs shrink-0 shadow-sm">
                AI
              </div>
              <div className="bg-slate-50 border border-slate-200 px-4 py-3 rounded-2xl rounded-bl-none flex items-center space-x-2">
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:0.2s]" />
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:0.4s]" />
                <span className="text-[11px] text-slate-500 ml-2">Retrieving & verifying legal evidence...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-slate-200 bg-slate-50/50">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex gap-2"
          >
            <label htmlFor="chat-query-input" className="sr-only">
              Ask a legal query grounded in your documents
            </label>
            <input
              id="chat-query-input"
              type="text"
              value={inputContent}
              onChange={(e) => setInputContent(e.target.value)}
              placeholder="Ask a legal query grounded in your documents..."
              aria-label="Ask a legal query grounded in your documents"
              disabled={isSending}
              className="flex-1 px-4 py-2.5 text-xs bg-white border border-slate-300 rounded-lg placeholder:text-slate-500 text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition disabled:bg-slate-100"
            />
            <button
              type="submit"
              disabled={!inputContent.trim() || isSending}
              aria-label="Send message"
              className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white rounded-lg font-medium text-xs flex items-center gap-1.5 transition shrink-0 shadow-xs"
            >
              <Send className="h-3.5 w-3.5" aria-hidden="true" />
              <span>Send</span>
            </button>
          </form>
          <p className="text-[10px] text-slate-600 text-center mt-2">
            Non-negotiable Disclaimer: LEGAL AI provides legal research assistance only and does not constitute formal legal counsel.
          </p>
        </div>

        {/* Citation Inspector Drawer / Modal */}
        {selectedCitation && (
          <div className="absolute inset-y-0 right-0 w-96 bg-white border-l border-slate-200 shadow-xl z-20 flex flex-col p-5 overflow-y-auto animate-in slide-in-from-right duration-200">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-emerald-700" aria-hidden="true" />
                <h3 className="font-bold text-slate-900 text-sm">
                  Citation Inspector [{selectedCitation.citation_order}]
                </h3>
              </div>
              <button
                onClick={() => setSelectedCitation(null)}
                aria-label="Close citation inspector"
                className="text-slate-500 hover:text-slate-700 p-1 rounded-md transition"
              >
                <X className="h-4 w-4" aria-hidden="true" />
              </button>
            </div>

            <div className="mt-4 space-y-4 text-xs">
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-100 space-y-1">
                <div className="text-[11px] text-slate-600 uppercase font-semibold">Source Document</div>
                <div className="font-medium text-slate-800 flex items-center gap-1.5">
                  <FileText className="h-3.5 w-3.5 text-indigo-600 shrink-0" aria-hidden="true" />
                  <span className="truncate">{selectedCitation.document_title || 'Document Record'}</span>
                </div>
                <div className="text-slate-600 text-[11px] pt-1">
                  Page Number: <strong className="text-slate-800">{selectedCitation.page_number}</strong>
                </div>
              </div>

              <div>
                <div className="text-[11px] text-slate-600 uppercase font-semibold mb-1.5">
                  Verbatim Evidentiary Excerpt
                </div>
                <blockquote className="p-3 bg-amber-50/70 border-l-4 border-amber-400 rounded-r-lg text-slate-800 font-serif italic text-xs leading-relaxed">
                  "{selectedCitation.quoted_text}"
                </blockquote>
              </div>

              <div className="pt-2">
                <div className="flex items-center gap-2 p-2.5 rounded-lg bg-emerald-50 border border-emerald-100 text-emerald-900 text-[11px]">
                  <ShieldCheck className="h-4 w-4 text-emerald-700 shrink-0" aria-hidden="true" />
                  <span>
                    Claim-Level Verification: This quote directly supports the corresponding factual claim.
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
