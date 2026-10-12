// 한 번 만들고 값만 갱신하는 선택 그룹. 버튼을 다시 만들지 않으므로 키보드 포커스가 유지된다.
import { h } from './dom.js';

export function createChoiceGroup(container, { options, buttonClass, countClass, onSelect }) {
  const refs = new Map();
  for (const { value, label } of options) {
    const count = h('span', { class: countClass }, '0');
    const button = h('button', {
      type: 'button',
      class: buttonClass,
      'aria-pressed': 'false',
      onclick: () => onSelect(value),
    }, h('span', {}, label), count);
    refs.set(value, { button, count });
    container.appendChild(button);
  }
  return {
    update(selected, counts) {
      for (const [value, { button, count }] of refs) {
        button.setAttribute('aria-pressed', value === selected ? 'true' : 'false');
        count.textContent = String(counts && counts[value] !== undefined ? counts[value] : 0);
      }
    },
  };
}
