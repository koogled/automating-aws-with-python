# -*- coding: utf-8 -*-

"""Classes for AWS Certificates."""


class CertificateManager:
    """Manager an ACM Certificate."""

    def __init__(self, session):
        """Initialize CertificateManager."""
        self.session = session
        self.client = self.session.client('acm', region_name='us-east-1')

    def cert_matches(self, cert_arn, domain_name):
        """Find a cert to use."""
        cert_details = self.client.describe_certificate(
            CertificateArn=cert_arn)
        sans = cert_details['Certificate']['SubjectAlternativeNames']
        for cert_name in sans:
            if cert_name == domain_name:
                return True
            if cert_name[0] == '*' and domain_name.endswith(cert_name[1:]):
                return True
        return False

    def find_matching_cert(self, domain_name):
        """Find a cert that matches."""
        paginator = self.client.get_paginator('list_certificates')
        for page in paginator.paginate(CertificateStatuses=['ISSUED']):
            for cert in page['CertificateSummaryList']:
                if self.cert_matches(cert['CertificateArn'], domain_name):
                    return cert

        return None
