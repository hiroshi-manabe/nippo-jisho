(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.NippoQuickEdit = api;
}(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  const VOWEL_CYCLES = [
    ['a', 'ã', 'à', 'á', 'â'],
    ['e', 'ẽ', 'è', 'é', 'ê'],
    ['i', 'ĩ', 'ì', 'í', 'î'],
    ['o', 'õ', 'ò', 'ó', 'ô', 'ǒ'],
    ['u', 'ũ', 'ù', 'ú', 'û', 'ǔ'],
  ];
  const DELETABLE = new Set([' ', '-', ',', '.']);

  function parse(value) {
    const characters = [];
    let style = null;
    for (let index = 0; index < value.length; index++) {
      const character = value[index];
      if (character === '[' || character === '{') {
        if (style !== null) return {valid: false, error: 'Typeface spans cannot be nested or overlap.'};
        style = character === '[' ? 'roman' : 'italic';
      } else if (character === ']' || character === '}') {
        const expected = character === ']' ? 'roman' : 'italic';
        if (style !== expected) return {valid: false, error: 'A typeface span has an unmatched or mismatched delimiter.'};
        style = null;
      } else {
        characters.push({character, style});
      }
    }
    if (style !== null) return {valid: false, error: 'A typeface span has no closing delimiter.'};
    return {valid: true, characters, text: characters.map(item => item.character).join('')};
  }

  function serialize(characters) {
    let result = '';
    let style = null;
    const close = () => { if (style) result += style === 'roman' ? ']' : '}'; };
    for (const item of characters) {
      if (item.style !== style) {
        close();
        style = item.style;
        if (style) result += style === 'roman' ? '[' : '{';
      }
      result += item.character;
    }
    close();
    return result;
  }

  function replace(value, start, end, replacement, replacementStyle) {
    const parsed = parse(value);
    if (!parsed.valid) return value;
    const inherited = replacementStyle === undefined
      ? (parsed.characters[start]?.style || parsed.characters[start - 1]?.style || null)
      : replacementStyle;
    const inserted = Array.from(replacement).map(character => ({character, style: inherited}));
    parsed.characters.splice(start, end - start, ...inserted);
    return serialize(parsed.characters);
  }

  function toggleRoman(value, index) {
    const parsed = parse(value);
    if (!parsed.valid || !parsed.characters[index]) return value;
    parsed.characters[index].style = parsed.characters[index].style === 'roman' ? null : 'roman';
    return serialize(parsed.characters);
  }

  function uppercasePeriodTokenRange(value, index) {
    const parsed = parse(value);
    if (!parsed.valid || !parsed.characters[index]) return null;
    const character = parsed.characters[index].character;
    if (!/\p{Lu}/u.test(character) || (index > 0 && /\p{L}/u.test(parsed.characters[index - 1].character))) return null;
    let end = index + 1;
    while (end < parsed.characters.length && /\p{L}/u.test(parsed.characters[end].character)) end++;
    if (parsed.characters[end]?.character !== '.') return null;
    return {start: index, end: end + 1};
  }

  function typefaceTokenRange(value, index) {
    const uppercase = uppercasePeriodTokenRange(value, index);
    if (uppercase) return uppercase;
    const parsed = parse(value);
    if (!parsed.valid || !parsed.characters[index]) return null;
    const character = parsed.characters[index].character;
    if (!/\p{Ll}/u.test(character) || (index > 0 && /\p{L}/u.test(parsed.characters[index - 1].character))) return null;
    if (character === 'a') return null;
    const next = parsed.characters[index + 1]?.character;
    if (/\p{L}/u.test(next || '')) return null;
    return {start: index, end: index + (next === '.' ? 2 : 1)};
  }

  function toggleTypefaceRange(value, start, end, originalTypefaces) {
    const parsed = parse(value);
    if (!parsed.valid || start < 0 || end > parsed.characters.length || start >= end) return value;
    const current = parsed.characters[start].style || originalTypefaces[start] || 'roman';
    const target = current === 'italic' ? 'roman' : 'italic';
    for (let index = start; index < end; index++) {
      parsed.characters[index].style = originalTypefaces[index] === target ? null : target;
    }
    return serialize(parsed.characters);
  }

  function nextSForm(current, original) {
    const cycles = original === 'ſ' ? ['ſ', 's', 'f'] : (original === 'f' ? ['f', 'ſ'] : ['s', 'ſ']);
    const index = cycles.indexOf(current);
    return cycles[(index < 0 ? 0 : index + 1) % cycles.length];
  }

  function nextGQ(current) {
    if (current === 'g') return 'q';
    if (current === 'q') return 'g';
    if (current === 'G') return 'Q';
    if (current === 'Q') return 'G';
    return current;
  }

  function nextNM(current) {
    if (current === 'n') return 'm';
    if (current === 'm') return 'n';
    return current;
  }

  function nasalizedVowel(character) {
    return ({a: 'ã', e: 'ẽ', i: 'ĩ', o: 'õ', u: 'ũ'})[character] || null;
  }

  function nextPostvocalicNasal(current, original, previous, next) {
    const nasalized = nasalizedVowel(previous);
    if (!nasalized || (next && /[aeiouáéíóúàèìòùâêîôûãẽĩõũǒǔ]/u.test(next))) {
      return {kind: 'replace', value: nextNM(current)};
    }
    const alternate = nextNM(original);
    if (current === original) return {kind: 'replace', value: alternate};
    if (current === alternate) return {kind: 'contract', value: nasalized};
    return {kind: 'replace', value: current};
  }

  function nextCedilla(current) {
    if (current === 'c') return 'ç';
    if (current === 'ç') return 'c';
    return current;
  }

  function nextUV(current, original) {
    if (original !== 'u' && original !== 'v') return current;
    const accents = VOWEL_CYCLES.find(cycle => cycle[0] === 'u').slice(1);
    const cycle = original === 'v' ? ['v', 'u'] : ['u', 'v', ...accents];
    const index = cycle.indexOf(current);
    return index < 0 ? current : cycle[(index + 1) % cycle.length];
  }

  function nextIJ(current, original) {
    if (original !== 'i' && original !== 'j') return current;
    const accents = VOWEL_CYCLES.find(cycle => cycle[0] === 'i').slice(1);
    const cycle = original === 'j' ? ['j', 'i'] : ['i', 'j', ...accents];
    const index = cycle.indexOf(current);
    return index < 0 ? current : cycle[(index + 1) % cycle.length];
  }

  function vowelCycleForOriginal(original) {
    const lower = original.toLocaleLowerCase('und');
    const cycle = VOWEL_CYCLES.find(items => items.includes(lower));
    if (!cycle) return null;
    const pairedMarks = ({'ǒ': 'ô', 'ô': 'ǒ', 'ǔ': 'û', 'û': 'ǔ'});
    const paired = pairedMarks[lower];
    if (!paired) return cycle;
    return [lower, paired, ...cycle.filter(item => item !== lower && item !== paired)];
  }

  function nextVowel(current, original = current) {
    const lower = current.toLocaleLowerCase('und');
    const cycle = vowelCycleForOriginal(original);
    if (!cycle || !cycle.includes(lower)) return current;
    const next = cycle[(cycle.indexOf(lower) + 1) % cycle.length];
    return current === current.toLocaleUpperCase('und') ? next.toLocaleUpperCase('und') : next;
  }

  function align(before, current) {
    const rows = before.length + 1;
    const columns = current.length + 1;
    const cost = Array.from({length: rows}, () => Array(columns).fill(0));
    for (let i = 0; i < rows; i++) cost[i][0] = i;
    for (let j = 0; j < columns; j++) cost[0][j] = j;
    for (let i = 1; i < rows; i++) {
      for (let j = 1; j < columns; j++) {
        const substitution = cost[i - 1][j - 1] + (before[i - 1] === current[j - 1] ? 0 : 1);
        cost[i][j] = Math.min(substitution, cost[i - 1][j] + 1, cost[i][j - 1] + 1);
      }
    }
    const reversed = [];
    let i = before.length;
    let j = current.length;
    while (i || j) {
      const diagonal = i && j && cost[i][j] === cost[i - 1][j - 1] + (before[i - 1] === current[j - 1] ? 0 : 1);
      if (diagonal) {
        reversed.push({kind: before[i - 1] === current[j - 1] ? 'match' : 'substitute', beforeIndex: i - 1, currentIndex: j - 1});
        i--; j--;
      } else if (i && cost[i][j] === cost[i - 1][j] + 1) {
        reversed.push({kind: 'delete', beforeIndex: i - 1, currentIndex: j});
        i--;
      } else {
        reversed.push({kind: 'insert', beforeIndex: null, currentIndex: j - 1});
        j--;
      }
    }
    const operations = reversed.reverse();
    const currentToBase = Array(current.length).fill(null);
    const changed = Array(current.length).fill(false);
    const deletions = [];
    for (const operation of operations) {
      if (operation.kind === 'match' || operation.kind === 'substitute') {
        currentToBase[operation.currentIndex] = operation.beforeIndex;
        changed[operation.currentIndex] = operation.kind === 'substitute';
      } else if (operation.kind === 'insert') {
        changed[operation.currentIndex] = true;
      } else {
        deletions.push({...operation, character: before[operation.beforeIndex]});
      }
    }
    return {operations, currentToBase, changed, deletions};
  }

  return {VOWEL_CYCLES, DELETABLE, parse, serialize, replace, toggleRoman, uppercasePeriodTokenRange, typefaceTokenRange, toggleTypefaceRange, nextSForm, nextGQ, nextNM, nextPostvocalicNasal, nextCedilla, nextUV, nextIJ, vowelCycleForOriginal, nextVowel, align};
}));
