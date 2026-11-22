import { Link } from 'react-router-dom'

interface PlaceholderPageProps {
  titulo: string
}

export function PlaceholderPage({ titulo }: PlaceholderPageProps) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6">
      <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-8 text-center space-y-4">
        <h1 className="text-2xl font-semibold text-slate-900">{titulo}</h1>
        <p className="text-sm text-slate-500">
          Módulo configurado e pronto para implementação.
        </p>
        <Link
          to="/"
          className="inline-block rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 transition"
        >
          Voltar ao início
        </Link>
      </div>
    </div>
  )
}