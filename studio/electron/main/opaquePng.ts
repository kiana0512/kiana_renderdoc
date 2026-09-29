import { deflateSync, inflateSync } from 'node:zlib'

const signature = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])

function crc32(data: Buffer) {
  let crc = 0xffffffff
  for (const byte of data) {
    crc ^= byte
    for (let bit = 0; bit < 8; bit += 1) crc = (crc >>> 1) ^ ((crc & 1) ? 0xedb88320 : 0)
  }
  return (crc ^ 0xffffffff) >>> 0
}

function chunk(type: string, data: Buffer) {
  const name = Buffer.from(type, 'ascii')
  const output = Buffer.alloc(12 + data.length)
  output.writeUInt32BE(data.length, 0)
  name.copy(output, 4)
  data.copy(output, 8)
  output.writeUInt32BE(crc32(output.subarray(4, 8 + data.length)), 8 + data.length)
  return output
}

function paeth(left: number, above: number, upperLeft: number) {
  const prediction = left + above - upperLeft
  const leftDistance = Math.abs(prediction - left)
  const aboveDistance = Math.abs(prediction - above)
  const upperLeftDistance = Math.abs(prediction - upperLeft)
  return leftDistance <= aboveDistance && leftDistance <= upperLeftDistance ? left : aboveDistance <= upperLeftDistance ? above : upperLeft
}

/**
 * RenderDoc 的 RT PNG 保留原始 Alpha。很多 UE G-buffer/BackBuffer 的 Alpha 为 0，
 * 但 RGB 是有效的场景图像；浏览器直接显示会把这些 RGB 合成成黑色。
 * 只给预览副本把 Alpha 改为 255，原始 PNG 不动，方便继续检查 Alpha 通道。
 */
export function opaquePngPreview(input: Buffer): Buffer {
  if (!input.subarray(0, 8).equals(signature)) return input
  let offset = 8
  let header: Buffer | null = null
  const imageData: Buffer[] = []
  const metadata: Buffer[] = []
  while (offset + 12 <= input.length) {
    const length = input.readUInt32BE(offset)
    const end = offset + 12 + length
    if (end > input.length) return input
    const type = input.toString('ascii', offset + 4, offset + 8)
    const data = input.subarray(offset + 8, offset + 8 + length)
    if (type === 'IHDR') header = Buffer.from(data)
    if (type === 'IDAT') imageData.push(data)
    // 保留色彩空间和 ICC 元数据，避免只改 Alpha 却改变画面色调。
    if (['sRGB', 'gAMA', 'cHRM', 'iCCP', 'pHYs'].includes(type)) metadata.push(chunk(type, data))
    offset = end
    if (type === 'IEND') break
  }
  if (!header || header.length !== 13 || header[8] !== 8 || header[9] !== 6 || header[12] !== 0 || imageData.length === 0) return input
  const width = header.readUInt32BE(0)
  const height = header.readUInt32BE(4)
  const stride = width * 4
  if (!width || !height || stride * height > 512 * 1024 * 1024) return input
  const filtered = inflateSync(Buffer.concat(imageData))
  if (filtered.length !== (stride + 1) * height) return input
  const opaque = Buffer.alloc(filtered.length)
  let previous = Buffer.alloc(stride)
  for (let row = 0; row < height; row += 1) {
    const sourceOffset = row * (stride + 1)
    const filter = filtered[sourceOffset]
    if (filter > 4) return input
    const decoded = Buffer.alloc(stride)
    for (let x = 0; x < stride; x += 1) {
      const raw = filtered[sourceOffset + 1 + x]
      const left = x >= 4 ? decoded[x - 4] : 0
      const above = previous[x]
      const upperLeft = x >= 4 ? previous[x - 4] : 0
      const predictor = filter === 0 ? 0 : filter === 1 ? left : filter === 2 ? above : filter === 3 ? Math.floor((left + above) / 2) : paeth(left, above, upperLeft)
      decoded[x] = (raw + predictor) & 255
    }
    opaque[sourceOffset] = 0
    decoded.copy(opaque, sourceOffset + 1)
    for (let x = 3; x < stride; x += 4) opaque[sourceOffset + 1 + x] = 255
    previous = decoded
  }
  return Buffer.concat([signature, chunk('IHDR', header), ...metadata, chunk('IDAT', deflateSync(opaque, { level: 3 })), chunk('IEND', Buffer.alloc(0))])
}
