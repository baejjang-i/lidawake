// 아이콘 생성: npm i --no-save @resvg/resvg-js && node icon/make_icon.mjs
// 디자인: 살짝 열린 맥북 옆모습 — 쐐기형 본체(맥북 에어 옆선) + 18° 들린 덮개. 모노톤
// 출력: AppIcon.iconset/ (build.sh가 iconutil로 icns 변환), 메뉴 막대 템플릿 Lid{Open,Closed}Template(.png, @2x)
import { Resvg } from '@resvg/resvg-js'
import fs from 'fs'
import { fileURLToPath } from 'url'

const DIR = fileURLToPath(new URL('.', import.meta.url))
const REGULAR = { lid: 34, back: 84, front: 30, gap: 12 }
const BOLD = { lid: 46, back: 100, front: 38, gap: 26 }   // 메뉴 막대·32px 이하: 작게 보여도 덮개와 틈이 뭉개지지 않게

// 원점 = 본체 바닥 왼쪽(위가 음수). 열림: 덮개가 힌지에서 a도 들림 / 닫힘: 본체 윗면 기울기를 따라 누움
function laptop(open, color, { lid, back, front, gap }, len = 560, a = 18) {
  const slope = Math.atan((back - front) / len) * 180 / Math.PI
  const rot = `rotate(${open ? -a : slope} ${back / 2} ${-back / 2})`
  const lidRect = pad => `<rect x="${back / 2 - lid / 2 - pad}" y="${-back - gap - lid - pad}" width="${len - 14 + 2 * pad}" height="${lid + 2 * pad}" rx="${lid / 2 + pad}" transform="${rot}"/>`
  const base = `M${back / 2} ${-back} L${len - front / 2} ${-front} A${front / 2} ${front / 2} 0 0 1 ${len - front / 2} 0 L${back / 2} 0 A${back / 2} ${back / 2} 0 0 1 ${back / 2} ${-back}Z`
  // 덮개 둘레(gap)만큼 본체를 파내서 덮개와 본체를 분리 → 배경이 투명해도(메뉴 막대 템플릿) 틈이 보임
  return `<mask id="cut" maskUnits="userSpaceOnUse" x="-999" y="-999" width="2998" height="1998"><rect x="-999" y="-999" width="2998" height="1998" fill="#fff"/><g fill="#000">${lidRect(gap)}</g></mask>
  <path d="${base}" fill="${color}" mask="url(#cut)"/><g fill="${color}">${lidRect(0)}</g>`
}

const svg = (w, h, vb, inner) => `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="${vb}">${inner}</svg>`
const png = (s, name) => fs.writeFileSync(DIR + name, new Resvg(Buffer.from(s)).render().asPng())
const bbox = inner => {
  const b = new Resvg(Buffer.from(svg(4096, 4096, '0 0 4096 4096', `<g transform="translate(2000 2000)">${inner}</g>`))).getBBox()
  return { x: b.x - 2000, y: b.y - 2000, w: b.width, h: b.height }
}
// bbox 중심을 (cx, cy)에, w×h 안에 들어가게
const fit = (b, cx, cy, w, h) => {
  const s = Math.min(w / b.w, h / b.h)
  return `translate(${cx - (b.x + b.w / 2) * s} ${cy - (b.y + b.h / 2) * s}) scale(${s})`
}

// 앱 아이콘: macOS 그리드(1024 캔버스, 824 타일), 기호는 폭 560 안에서 시각 중심 y=500
const appIcon = size => {
  const g = laptop(true, '#fff', size <= 32 ? BOLD : REGULAR)
  return svg(size, size, '0 0 1024 1024', `
  <defs><filter id="sh" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="14"/></filter></defs>
  <rect x="100" y="114" width="824" height="824" rx="185" opacity=".35" filter="url(#sh)"/>
  <rect x="100" y="100" width="824" height="824" rx="185" fill="#111113"/>
  <g transform="${fit(bbox(g), 512, 500, 560, 460)}">${g}</g>`)
}
fs.mkdirSync(DIR + 'AppIcon.iconset', { recursive: true })
for (const s of [16, 32, 128, 256, 512])
  for (const k of [1, 2]) png(appIcon(s * k), `AppIcon.iconset/icon_${s}x${s}${k === 2 ? '@2x' : ''}.png`)

// 메뉴 막대: 22×16pt 캔버스. 켬/끔이 같은 변환을 써서 전환할 때 본체가 제자리에 있음
const open = laptop(true, '#000', BOLD), closed = laptop(false, '#000', BOLD)
const t = fit(bbox(open), 11, 8, 21, 14)
for (const [name, g] of [['LidOpenTemplate', open], ['LidClosedTemplate', closed]])
  for (const k of [1, 2]) png(svg(22 * k, 16 * k, '0 0 22 16', `<g transform="${t}">${g}</g>`), `${name}${k === 2 ? '@2x' : ''}.png`)

console.log('saved', DIR)
