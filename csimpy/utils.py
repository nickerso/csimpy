import libsedml


def get_xpath_namespaces(sed_element):
    """
    Get all the XML namespaces for the given SED-ML element. See https://github.com/fbergmann/libSEDML/issues/77 for
    an issue on getting the actual namespaces, but for now looks like this will only return namespaces declared on
    the root element of the SED-ML document.

    :param sed_element: the SED-ML element to define the context for fetching namespaces.
    :return: a dictionary of defined namespaces.
    """
    ns = {}
    xmlns = sed_element.getNamespaces()
    for n in range(0, xmlns.getNumNamespaces()):
        prefix = xmlns.getPrefix(n)
        # we can't use a default namespace in XPath so filter it out...
        if prefix != '':
            uri = xmlns.getURI(n)
            ns[prefix] = uri
    return ns
