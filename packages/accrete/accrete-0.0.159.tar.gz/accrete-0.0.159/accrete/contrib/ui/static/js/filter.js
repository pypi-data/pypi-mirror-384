document.addEventListener('alpine:init', () => {
    Alpine.data('filter', () => ({

        showParams: false,

        closeParams() {
            this.$el.active = false;
            this.showParams = false;
        },

        applyQuery(queryString = null) {
            const url = new URL(window.location);
            const queryApply = this.$refs.queryApply;
            const queryApplyEvent = new Event('click');
            const query = queryString || JSON.stringify(this.buildJsonQueryFromHtml());
            url.searchParams.set('q', query);
            url.searchParams.set('page', '1');
            queryApply.setAttribute('hx-get', url.toString());
            htmx.process(queryApply);
            queryApply.dispatchEvent(queryApplyEvent);
            this.$refs.filterInput.focus()
            if (this.$refs.filterInput.nodeName === 'INPUT') {
                this.$refs.filterInput.select();
            }
        },

        addTag() {
            if (this.$refs.filterInput.nodeName === 'INPUT' && !this.$refs.filterInput.reportValidity()) {
                return
            }
            const jsonQuery = this.buildJsonQueryFromHtml();
            const value = this.cleanValue(
                this.$refs.filterInput.value,
                this.$refs.filterInput.getAttribute('data-type')
            );
            jsonQuery.push({
                [this.$refs.filterLookup.value]: value}
            );
            const jsonQueryString = JSON.stringify(jsonQuery);
            this.applyQuery(jsonQueryString);
        },

        removeTag() {
            this.$el.parentElement.parentElement.setAttribute(
                'data-remove-from-query', 'true'
            );
            this.applyQuery();
        },

        groupTag() {
            this.$el.parentElement.parentElement.setAttribute(
                'data-group-tag', 'true'
            );
            this.applyQuery();
        },

        buildJsonQueryFromHtml(tagGroup=null) {
            const queryTags = (
                tagGroup || this.$refs.queryTags
            );
            let query = []
            if (!queryTags) {
                return query
            }
            for (let tag of queryTags.children) {
                if (tag.hasAttribute('data-remove-from-query')) {
                    continue
                }
                if (tag.classList.contains('query-group-container')) {
                    const operator = tag.querySelector('.query-operator').firstElementChild.firstElementChild.value;
                    const queryGroup = this.buildJsonQueryFromHtml(tag.querySelector('.query-group'))
                    if (queryGroup.length === 0) {
                        continue
                    }
                    if (query.length === 0) {
                        query = this.buildJsonQueryFromHtml(tag.querySelector('.query-group'));
                    }
                    else {
                        query.push(operator);
                        query.push(this.buildJsonQueryFromHtml(tag.querySelector('.query-group')));
                    }
                }
                else if (tag.classList.contains('query-tag-container')) {
                    if (query.length > 0) {
                        const operator = tag.querySelector('.query-operator');
                        query.push(operator.firstElementChild.firstElementChild.value);
                    }
                    const key = tag.getAttribute('data-lookup');
                    let value = tag.getAttribute('data-value');
                    let dataType = tag.getAttribute('data-type');
                    value = this.cleanValue(value, dataType);
                    if (tag.hasAttribute('data-group-tag')) {
                        query.push([{[key]: value}]);
                    }
                    else {
                        query.push({[key]: value});
                    }

                }
            }
            return query
        },

        cleanValue(value, dataType) {
            if (dataType === 'bool') {
                value = value.toLowerCase() === 'true'
            }
            return value
        },
    }))
})


function isObject(item) {
    return Object.prototype.toString.apply(item) === '[object Object]'
}


function isArray(item) {
    return Object.prototype.toString.apply(item) === '[object Array]'
}


function isString(item) {
    return Object.prototype.toString.apply(item) === '[object String]'
}

function isFirstQueryGroup(queryGroup) {
    return queryGroup.parentElement.id === 'query-tags'
}
