interface BrandLogoProps {
  subtitulo?: string
  tema?: 'claro' | 'escuro'
  tamanho?: 'sm' | 'md'
}

export function BrandLogo({
  subtitulo,
  tema = 'claro',
  tamanho = 'md',
}: BrandLogoProps) {
  const escuro = tema === 'escuro'
  const dimensao = tamanho === 'sm' ? 'h-8 w-8' : 'h-10 w-10'

  return (
    <div className="flex items-center gap-3 select-none">
      <img
        src="/logo.jpg"
        alt="LabManager"
        className={`${dimensao} rounded-lg object-cover ring-1 ${
          escuro ? 'ring-brand-400/25' : 'ring-brand-800/15'
        }`}
      />
      <div className="leading-none">
        <div className="flex items-baseline gap-0.5 text-[17px] tracking-tight">
          <span className={`font-bold ${escuro ? 'text-white' : 'text-ink'}`}>
            Lab
          </span>
          <span className={`font-medium ${escuro ? 'text-brand-400' : 'text-brand-800'}`}>
            Manager
          </span>
        </div>
        {subtitulo && (
          <span
            className={`block text-[11px] font-medium mt-1 ${
              escuro ? 'text-slate-400' : 'text-slate-500'
            }`}
          >
            {subtitulo}
          </span>
        )}
      </div>
    </div>
  )
}