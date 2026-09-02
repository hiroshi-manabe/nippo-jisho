(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.NippoKanaGuide = api;
}(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  const LABELS = new Set(['ad', 'adu', 'aduer', 'aduerb', 'alicubi', 'bup', 'fab', 'fei', 'feiq', 'fox', 'item', 'lib', 'melius', 'mon', 'nome', 'p', 'permet', 's', 'tac', 'taif', 'ut', 'vt', 'voi', 'x', 'xix']);
  const VOWELS = {a: 'ア', i: 'イ', u: 'ウ', e: 'エ', o: 'オ'};
  const ROWS = {
    k: ['カ', 'キ', 'ク', 'ケ', 'コ'], g: ['ガ', 'ギ', 'グ', 'ゲ', 'ゴ'], s: ['サ', 'シ', 'ス', 'セ', 'ソ'], z: ['ザ', 'ジ', 'ズ', 'ゼ', 'ゾ'],
    t: ['タ', 'チ', 'ツ', 'テ', 'ト'], d: ['ダ', 'ヂ', 'ヅ', 'デ', 'ド'], n: ['ナ', 'ニ', 'ヌ', 'ネ', 'ノ'], h: ['ハ', 'ヒ', 'フ', 'ヘ', 'ホ'],
    b: ['バ', 'ビ', 'ブ', 'ベ', 'ボ'], p: ['パ', 'ピ', 'プ', 'ペ', 'ポ'], m: ['マ', 'ミ', 'ム', 'メ', 'モ'], r: ['ラ', 'リ', 'ル', 'レ', 'ロ'],
    y: ['ヤ', 'イ', 'ユ', 'エ', 'ヨ'], w: ['ワ', 'ヰ', 'ウ', 'ヱ', 'ヲ']
  };
  const VOWEL_INDEX = {a: 0, i: 1, u: 2, e: 3, o: 4};
  const MARKED = {
    'à': ['a', 'ァ'], 'á': ['a', 'ァ'], 'â': ['a', 'ァ'], 'ǎ': ['a', 'ァ'], 'ì': ['i', 'ィ'], 'í': ['i', 'ィ'], 'î': ['i', 'ィ'], 'ǐ': ['i', 'ィ'],
    'ù': ['u', 'ゥ'], 'ú': ['u', 'ゥ'], 'û': ['u', 'ゥ'], 'ǔ': ['u', 'ゥ'], 'è': ['e', 'ェ'], 'é': ['e', 'ェ'], 'ê': ['e', 'ェ'], 'ě': ['e', 'ェ'],
    'ò': ['o', 'ォ'], 'ó': ['o', 'ォ'], 'ô': ['o', 'ゥ'], 'ǒ': ['o', 'ゥ']
  };
  const NASAL = {'ã': 'a', 'ĩ': 'i', 'ũ': 'u', 'ẽ': 'e', 'õ': 'o'};

  const normalized = value => value.normalize('NFC').toLocaleLowerCase('und');
  const isLabel = token => LABELS.has(normalized(token).replace(/[^a-z]/g, ''));

  function vowelAt(text, index) {
    const character = text[index];
    if (VOWELS[character]) return {base: character, suffix: ''};
    if (MARKED[character]) return {base: MARKED[character][0], suffix: MARKED[character][1]};
    if (NASAL[character]) return {base: NASAL[character], suffix: 'ン'};
    return null;
  }

  function palatalized(row, vowel) {
    const small = {a: 'ャ', u: 'ュ', o: 'ョ'}[vowel];
    return ROWS[row]?.[1] && small ? ROWS[row][1] + small : null;
  }

  function transliterateToken(token) {
    if (!token || isLabel(token)) return null;
    const text = normalized(token).replace(/ſ/g, 's');
    let output = '';
    let index = 0;
    while (index < text.length) {
      if (text[index] === 'u') {
        const following = vowelAt(text, index + 1);
        if (following) { output += ROWS.w[VOWEL_INDEX[following.base]] + following.suffix; index += 2; continue; }
      }
      if (text[index] === 'n' && (index + 1 === text.length || !vowelAt(text, index + 1))) { output += 'ン'; index++; continue; }
      let consonant = '';
      if (text.startsWith('tç', index)) { consonant = 't'; index += 2; }
      else if (text.startsWith('zz', index)) { consonant = 'z'; index += 2; }
      else if (text.startsWith('nh', index)) { consonant = 'ny'; index += 2; }
      else if (text.startsWith('ch', index)) { consonant = 'ch'; index += 2; }
      else if (text[index] === 'x') { consonant = 'sh'; index++; }
      else if (text[index] === 'q') { consonant = 'k'; index++; if (text[index] === 'u' && /[ie]/u.test(text[index + 1] || '')) index++; }
      else if (text[index] === 'c') { consonant = 'k'; index++; }
      else if (text[index] === 'ç') { consonant = 's'; index++; }
      else if (text[index] === 'f') { consonant = 'h'; index++; }
      else if (text[index] === 'j') { if (index + 1 === text.length) { output += 'イ'; index++; continue; } consonant = 'j'; index++; }
      else if (text[index] === 'v') {
        if (index === 0 && vowelAt(text, index + 1)) { index++; continue; }
        if (index === 0) { output += 'ウ'; index++; continue; }
        consonant = 'w'; index++;
      }
      else if (ROWS[text[index]]) { consonant = text[index]; index++; }
      else if (vowelAt(text, index)) { const vowel = vowelAt(text, index); output += VOWELS[vowel.base] + vowel.suffix; index++; continue; }
      else return null;

      if (text[index] === consonant && consonant.length === 1) { output += 'ッ'; index++; }
      if (text[index] === 'i' && ['k', 'g', 'n', 'h', 'b', 'p', 'm', 'r'].includes(consonant)) {
        const following = vowelAt(text, index + 1);
        const combined = following && palatalized(consonant, following.base);
        if (combined) { output += combined + following.suffix; index += 2; continue; }
      }
      const vowel = vowelAt(text, index);
      if (!vowel) return null;
      if (consonant === 'sh') output += {a: 'シャ', i: 'シ', u: 'シュ', e: 'シェ', o: 'ショ'}[vowel.base];
      else if (consonant === 'ch') output += {a: 'チャ', i: 'チ', u: 'チュ', e: 'チェ', o: 'チョ'}[vowel.base];
      else if (consonant === 'j') output += {a: 'ジャ', i: 'ジ', u: 'ジュ', e: 'ジェ', o: 'ジョ'}[vowel.base];
      else if (consonant === 'ny') output += {a: 'ニャ', i: 'ニ', u: 'ニュ', e: 'ニェ', o: 'ニョ'}[vowel.base];
      else output += ROWS[consonant]?.[VOWEL_INDEX[vowel.base]] || '';
      output += vowel.suffix;
      index++;
    }
    return output || null;
  }

  function convertRomanText(text) {
    let converted = false;
    const output = text.replace(/[A-Za-zÀ-žǍ-ǔſç]+/gu, token => {
      if (isLabel(token)) return '';
      const kana = transliterateToken(token);
      if (!kana) return token;
      converted = true;
      return kana;
    });
    const cleaned = output.replace(/(^|\s)[,;]\s*/gu, '$1').replace(/\s+/gu, ' ');
    return converted && cleaned.trim() ? cleaned : null;
  }

  function convertRuns(runs) {
    if (!runs.some(run => run.typeface === 'roman') || !runs.some(run => run.typeface === 'italic')) return null;
    let converted = false;
    const output = runs.map(run => {
      if (run.typeface !== 'roman') return '';
      const kana = convertRomanText(run.text);
      if (!kana) return run.text.replace(/[A-Za-zÀ-žǍ-ǔſç]+/gu, '');
      converted = true;
      return kana;
    }).join('').replace(/\s+/gu, ' ').trim();
    return converted && output ? output : null;
  }

  return {convertRomanText, convertRuns, transliterateToken};
}));
