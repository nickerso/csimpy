import libsedml


def get_xpath_namespaces(sed_element):
    """
    Get all the XML namespaces for the given SED-ML element. See https://github.com/fbergmann/libSEDML/issues/77 for
    some background. This will collect all namespaces from the current element and all its parents.

    :param sed_element: the SED-ML element to define the context for fetching namespaces.
    :return: a dictionary of defined namespaces.
    """
    ns = {}
    current_sed_base = sed_element
    while current_sed_base:
        xmlns = current_sed_base.getElementNamespaces()
        if xmlns:
            for n in range(0, xmlns.getNumNamespaces()):
                prefix = xmlns.getPrefix(n)
                if prefix == '':
                    # we can't use a default namespace in XPath so filter it out...
                    continue
                elif prefix in ns:
                    # existing namespace prefixes should not be changed
                    continue
                else:
                    uri = xmlns.getURI(n)
                    ns[prefix] = uri
        current_sed_base = current_sed_base.getParentSedObject()
    return ns
